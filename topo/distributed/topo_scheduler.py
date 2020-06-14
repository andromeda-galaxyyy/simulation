from topo.distributed.topobuilder import TopoBuilder
from typing import Dict, List
import time
from threading import Thread
import threading
from utils.log_utils import debug, info
from path_utils import get_prj_root
import os
from utils.file_utils import load_pkl
import signal
from sockets.client import send
import json

static_dir = os.path.join(get_prj_root(), "static")
topos_pkl = os.path.join(static_dir, "satellite_overall.pkl")


class Scheduler:
	def __init__(self, worker_id: int, config: Dict, topos: List, builder: TopoBuilder):
		self.topos = [t["topo"] for t in topos]
		self.durations = [t["duration"] for t in topos]
		self.builder = builder
		self.scheduler_id = -1
		self.cv = threading.Condition()
		self.config = config
		self.worker_id = worker_id

	def _do_scheduler(self):
		ts_idx = 0
		self.scheduler_id = threading.get_ident()
		debug("Start scheduler thread with thread id {}".format(self.scheduler_id))

		self.cv.acquire()
		while True:
			info("new topo idx {}".format(ts_idx))
			topo = self.topos[ts_idx]
			duration = self.durations[ts_idx]

			self.builder.diff_topo(topo)
			if self.worker_id == 0:
				self.report_topo_idx(ts_idx)
			# The return value is True unless a given timeout expired, in which case it is False
			# timeout expired,false,continue to next topo
			if not self.cv.wait(duration):
				ts_idx = (ts_idx + 1) % 44
				continue
			else:
				debug("Exit scheduler")
				break

	def report_topo_idx(self, idx):
		ip = self.config["controller"].split(":")[0]
		port = self.config["topo_port"]
		obj = {"topo_idx": idx}
		threading.Thread(target=send, args=(ip, port, json.dumps(obj))).start()

	def start(self):
		debug("Topo scheduler started")
		Thread(target=self._do_scheduler).start()

	def stop(self):
		debug("Stop requested...")
		self.cv.acquire()
		self.cv.notify()
		self.cv.release()
		self.cv = threading.Condition()


if __name__ == '__main__':
	topos = load_pkl(topos_pkl)
	scheduler = Scheduler(topos, None)
	scheduler.start()


	def sigint_handler(signum, frame):
		scheduler.stop()
		exit(-1)


	signal.signal(signal.SIGINT, sigint_handler)
	while True:
		time.sleep(1)
