from typing import Dict, List
import threading
import subprocess
import time
import os
from path_utils import get_prj_root

target_id_dir = os.path.join(get_prj_root(), "topo/distributed/targetids")


def run_ns_binary(ns: str, bin: str, params: str, log_fn: str = "/tmp/log.log"):
	os.system("ip netns exec {} nohup {} {} >{} 2>&1 &".format(ns, bin, params, log_fn))


def kill_pid(pid):
	os.system("kill -9 {}".format(pid))


class TrafficManager:
	def __init__(self, config: Dict, hostids: List[int]):
		self.generator_id = 0
		self.config = config
		self.hostids = hostids
		self.cv = threading.Condition()

		self.processes = {
			"iot": [],
			"video": [],
			"voip": []
		}
		self.genid2pid = {}
		self.pid2genid = {}
		self.binary = self.config["traffic_generator"]

	def start_traffic(self, hid, flow_type) -> (int, int):
		hostname = "h{}".format(hid)
		intf = "{}-eth0".format(hostname)
		target_id_fn = os.path.join(target_id_dir, "{}.targetids".format(hostname))
		gen_id = self.generator_id
		self.generator_id += 1
		log_fn = "/tmp/{}.{}.gen.log".format(hostname, gen_id)
		pkt_dir = self.config["traffic_dir"][flow_type]

		params = "--id {} " \
		         "--dst_id {} " \
		         "--pkts {} " \
		         "--mtu {} " \
		         "--int {} " \
		         "--cip {} " \
		         "--cport {}".format(
			hid,
			target_id_fn,
			pkt_dir,
			self.config["vhost_mtu"],
			intf,
			self.config["controller_ip"],
			self.config["controller_socket_port"],
		)
		commands = "nohup {} {} >{} 2>&1 &".format(self.binary, params, log_fn)
		pid = subprocess.Popen(list(commands.split(" "))).pid
		return pid, self.generator_id

	def start(self):
		flow_types=["iot","video","voip"]
		for ft in flow_types:
			for _ in range(self.config["num_process"][ft][0]):
				for hid in self.hostids:
					pid,genid=self.start_traffic(hid,ft)
					self.pid2genid[pid]=genid
					self.genid2pid[genid]=pid
					self.processes[ft].append(pid)


		self.cv.acquire()
		#先产生small模式的流量
		#在此基础上产生medium模式的流量
		# 产生large模式的流量

		while True:
			#按照一定的模式产生流量
			pass


	def stop(self):
		self.cv.acquire()
		self.cv.notify()






if __name__ == '__main__':
	manager=TrafficManager()
