from logging import StrFormatStyle
import os

from argparse import ArgumentParser
from utils.file_utils import check_dir, check_file, load_json, load_pkl
from path_utils import get_prj_root
from utils.log_utils import debug, info, err
from utils.common_utils import is_digit
from topo.distributed.topo_scheduler import Scheduler2
from typing import Dict, List
from utils.process_utils import start_new_thread_and_run
import requests
import threading

tmp_dir = os.path.join(get_prj_root(), "topo/distributed/tmp")
iptables_bk = os.path.join(tmp_dir, "iptables.bk")
static_dir = os.path.join(get_prj_root(), "static")
topos_pkl = os.path.join(static_dir, "satellite_overall.pkl")


def do_post(url, obj):
	requests.post(url, json=obj)


def do_delete(url):
	requests.delete(url)


class traffic_timer:
	def __init__(self, config: Dict) -> None:
		self.config = config
		self.cv = threading.Condition()
		self.traffic_scales = self.config["traffic_mode"]
		self.durations = self.config["traffic_duration"]
		self.started = False
		assert len(self.traffic_scales) == len(self.durations)

	def __do_start(self):
		traffic_scale_idx = 0
		scales = self.traffic_scales
		durations = self.durations
		obj = {
			"mode": ""
		}
		self.cv.acquire()
		while True:
			scale = scales[traffic_scale_idx]
			duration = durations[traffic_scale_idx]
			obj["mode"] = scale
			debug("traffic mode change to {}".format(scale))
			for idx, ip in enumerate(self.config["manage_ip"]):
				url = "http://{}:{}/traffic2".format(ip, 5000)
				start_new_thread_and_run(do_post, [url, obj])
			# threading.Thread(target=do_post, args=[url, obj]).start()

			# sleep
			if not self.cv.wait(duration):
				traffic_scale_idx = (traffic_scale_idx + 1) % (len(durations))
				continue
			else:
				debug("Exit traffic mode timer")
				self.cv.release()
				break

	def start(self):
		threading.Thread(target=self.__do_start).start()
		self.started = True

	def __do_stop(self):
		self.cv.acquire()
		self.cv.notify()
		self.cv.release()
		for idx, ip in enumerate(self.config["manage_ip"]):
			url = "http://{}:{}/traffic2".format(ip, 5000)
			threading.Thread(target=do_delete, args=[url]).start()

	def stop(self):
		self.__do_stop()
		self.started = False


traffictimer = None


def cli(topos: List, config: Dict, scheduler: Scheduler2):
	traffic_started = False
	while True:
		os.system("clear")
		try:
			print("> Available commands:\n"
			      "> 0.set up local switch\n"
			      "> 1.start topo scheduler\n"
			      "> 2.stop topo scheduler\n"
			      "> 3.start telemetry\n"
			      "> 4.stop telemetry\n"
			      "> 5.start traffic scheduler\n"
			      "> 6.stop traffic scheduler\n"
			      "> 7.quit\n"
			      "> 8.set up first topo\n"
			      "> 9.set up supplementary topo\n"
			      "> 10.(experimental) start traffic actor\n"
			      "> 11.(experimental) stop traffic actor\n"
			      "> 12. start classifier demo\n"
			      "> 13. stop classifier demo\n"
			      "> 14. setup military supplementary topo 10Mbps\n"
			      "> 15. setup military supplementary topo 5Mbps\n" 
			      "> #############\n"
			      "> 16. setup anomaly supplementary topo\n"
			      "> #############\n"
			      "> 17. start flow printer\n"
			      "> 18. stop flow printer\n"
			      "> Press Enter to print this msg")

			command = input(">Input commands:\n").strip()
			if len(command) == 0:
				os.system("clear")
				continue
			if not is_digit(command):
				os.system("clear")
				continue

			command = int(command)

			if command==17:
				for idx,ip in enumerate(config["manage_ip"]):
					url="http://{}:{}/printer".format(ip,5000)
					start_new_thread_and_run(do_post,[url,{"data":"nothing"}])
					continue

			if command==18:
				for idx,ip in enumerate(config["manage_ip"]):
					url="http://{}:{}/printer".format(ip,5000)
					start_new_thread_and_run(do_delete,[url,{"data":"nothing"}])
					continue

			if command==12:
				for idx,ip in enumerate(config["manage_ip"]):
					url="http://{}:{}/classifier".format(ip,5000)
					start_new_thread_and_run(do_post,[url,{"data":"nothing"}])
					continue
			if command==13:
				for idx,ip in enumerate(config["manage_ip"]):
					url="http://{}:{}/classifier".format(ip,5000)
					start_new_thread_and_run(do_delete,[url])
					continue

			if command==14:
				for idx,ip in enumerate(config["manage_ip"]):
					url="http://{}:{}/supplementary2".format(ip,5000)
					start_new_thread_and_run(do_post,[url,{"band":10}])
					continue

			if command==15:
				for idx,ip in enumerate(config["manage_ip"]):
					url="http://{}:{}/supplementary2".format(ip,5000)
					start_new_thread_and_run(do_post,[url,{"band":5}])
					continue

			if command==16:
				for idx,ip in enumerate(config["manage_ip"]):
					url="http://{}:{}/anomaly".format(ip,5000)
					start_new_thread_and_run(do_post,[url,{"band":5}])
					continue

			if command == 0:
				intfs = config["workers_intf"]
				# set up local switch
				for idx, ip in enumerate(config["manage_ip"]):
					url = "http://{}:{}/config".format(ip, 5000)
					intf = intfs[idx]
					start_new_thread_and_run(do_post,
					                         [url, {"config": config, "id": idx, "intf": intf}])
				# threading.Thread(target=do_post, args=[url, {"config": config, "id": idx,
				#                                             "intf": intf}]).start()
				continue
			if command == 8:
				for idx, ip in enumerate(config["manage_ip"]):
					url = "http://{}:{}/topo".format(ip, 5000)
					# threading.Thread(target=do_post, args=[url, {"topo": topos[0]["topo"]}]).start()
					start_new_thread_and_run(do_post, [url, {"topo": topos[0]["topo"]}])
				continue

			if command == 1:
				debug("Topo scheduler started")
				scheduler.start()
				continue

			if command == 2:
				debug("Topo scheduler stoped")
				scheduler.stop()
				continue

			if command == 3:
				debug("Start telemetry")
				for idx, ip in enumerate(config["manage_ip"]):
					url = "http://{}:{}/telemetry".format(ip, 5000)
					start_new_thread_and_run(do_post, [url, {}])
				continue

			if command == 5:
				for idx, ip in enumerate(config["manage_ip"]):
					url = "http://{}:{}/traffic".format(ip, 5000)
					# threading.Thread(target=do_post, args=[url, {}]).start()
					start_new_thread_and_run(do_post, [url, {}])
					continue

			if command == 6:
				for idx, ip in enumerate(config["manage_ip"]):
					url = "http://{}:{}/traffic".format(ip, 5000)
					# threading.Thread(target=do_delete, args=[url]).start()
					start_new_thread_and_run(do_delete, [url])
					continue

			if command == 7:
				scheduler.stop()
				global traffictimer
				traffictimer.stop()
				traffictimer=traffic_timer(config)
				for idx, ip in enumerate(config["manage_ip"]):
					url = "http://{}:{}/config".format(ip, 5000)
					start_new_thread_and_run(do_delete, [url])
				# threading.Thread(target=do_delete, args=[url]).start()
				continue
			if command == 9:
				worker_ips = config["manage_ip"]
				# set up server access point
				url1 = "http://{}:{}/supplementary".format(worker_ips[0], 5000)
				start_new_thread_and_run(do_post, [url1, {"server": True}])
				# threading.Thread(target=do_post, args=[url1, {"server": True}]).start()

				# url2 = "http://{}:{}/supplementary".format(worker_ips[0], 5000)
				# # threading.Thread(target=do_post, args=[url2, {"server": False}]).start()
				# start_new_thread_and_run(do_post, [url2, {"server": False}])
				continue

			if command == 10:
				traffictimer.start()
				continue

			if command == 11:
				traffictimer.stop()
				traffictimer = traffic_timer(config)
				continue

		except KeyboardInterrupt:
			# print(">Preparing quit. Clean up")
			# scheduler.stop()
			# traffictimer.stop()
			# for idx, ip in enumerate(config["workers_ip"]):
			# 	url = "http://{}:{}/config".format(ip, 5000)
			# 	threading.Thread(target=do_delete, args=[url]).start()
			break


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("--config", type=str, help="config file name",
	                    default="/home/stack/code/simulation/topo/distributed/telemetry.config.json")
	parser.add_argument("--topos_fn", type=str, help="Topo json file",
	                    default=topos_pkl)
	args = parser.parse_args()
	topos = load_pkl(args.topos_fn)
	config = load_json(args.config)
	scheduler = Scheduler2(config, topos)
	traffictimer = traffic_timer(config)
	cli(topos, config, scheduler)
