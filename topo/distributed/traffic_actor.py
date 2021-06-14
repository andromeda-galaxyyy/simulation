from typing import Dict, List
import threading
import subprocess
import time
import os
from path_utils import get_prj_root
import threading
from utils.log_utils import debug, info, err
import signal
from collections import defaultdict
import math
from subprocess import DEVNULL
from utils.file_utils import *
import random
from utils.process_utils import run_ns_process_background, kill_pid

target_id_dir = os.path.join(get_prj_root(), "topo/distributed/targetids")


# def run_ns_binary(ns: str, bin: str, params: str, log_fn: str = "/tmp/log.log"):
# 	os.system("ip netns exec {} nohup {} {} >{} 2>&1 &".format(
# 		ns, bin, params, log_fn))


# def kill_pid(pid):
# 	os.system("kill {}".format(pid))


class TrafficActor:
	def __init__(self, config: Dict, hostids: List[int]):
		self.hostids = hostids
		self.prev_mode = None
		self.config = config

		self.cnt = 0

		self.generator_id = 0
		self.genid2pid = {}
		self.pid2genid = {}
		self.processes = {
			"iot": [],
			"video": [],
			"voip": [],
			# "ar":[],
			# "ar":[],
		}
		self.binary = self.config["traffic_generator"]

		# self.traffic_scales = ["small", "small", "small", "small"]
		self.traffic_scales = self.config["traffic_mode"]
		self.durations = self.config["traffic_duration"]
		assert len(self.traffic_scales) == len(self.durations)
		# self.durations = [120, 120, 120, 120]
		# self.flow_types = ["video", "iot", "voip","ar"]
		self.flow_types = ["video", "iot", "voip"]

		self.schedule_record = []
		random.seed(int(time.time()))
		gen_base_log_dir = config["generator_log_dir"]
		del_dir(gen_base_log_dir)
		create_dir(gen_base_log_dir)

	def _do_start_traffic(self, hid, flow_type) -> (int, int):
		flowcounter_config = self.config["flowcounter"]
		redis_ip = flowcounter_config["redis_ip"]
		redis_port = flowcounter_config["redis_port"]
		hostname = "h{}".format(hid)
		intf = "{}-eth0".format(hostname)
		target_id_fn = os.path.join(target_id_dir, "{}.targetids".format(hostname))
		gen_id = self.generator_id
		self.generator_id += 1
		log_fn = "/tmp/{}.{}.gen.log".format(hostname, gen_id)
		pkt_dir = self.config["traffic_dir"][flow_type]
		ftype = -1
		report = False
		vlanid = -1
		nworkers = 1
		store_flow_counter = False
		if flow_type == "video":
			ftype = 0
			# report=True
			vlanid = 0
		elif flow_type == "iot":
			store_flow_counter = True
			nworkers = 8
			ftype = 1
			vlanid = 1
		elif flow_type == "voip":
			ftype = 2
			vlanid = 2
		elif flow_type == "ar":
			ftype = 3
			vlanid = 3
		else:
			raise Exception("Unsupported flow type")

		# report=True
		controller_ip = self.config["controller"].split(":")[0]
		enable_loss = (int(self.config["enable_loss"]) == 1)

		base_dir = self.config["generator_log_dir"]

		loss_dir = os.path.join(base_dir, "{}.tx.loss".format(hid))

		params = "--id {} " \
		         "--dst_id {} " \
		         "--pkts {} " \
		         "--mtu {} " \
		         "--int {} " \
		         "--cip {} " \
		         "--ftype {} " \
		         "--cport {} " \
		         "{} " \
		         "--loss_dir {} " \
		         "{} " \
		         "{} " \
		         "--workers {} " \
		         "{} " \
				 "--stats " \
		         "--rip {}".format(
			hid,
			target_id_fn,
			pkt_dir,
			self.config["vhost_mtu"],
			intf,
			controller_ip,
			ftype,
			self.config["controller_socket_port"],
			("--loss" if enable_loss else ""),
			(loss_dir if enable_loss else ""),
			("--report" if report else ""),
			("{}".format("--vlan {}".format(vlanid) if not report else "")),
			nworkers,
			"--storefcounter" if store_flow_counter else "",
			redis_ip,
		)

		commands = "{} {}".format(self.binary, params)

		enable_log = (int(self.config["enable_traffic_generator_log"]) == 1)
		if enable_log:
			# fp = open(log_fn, "w")
			# pid = subprocess.Popen(commands.split(" "), stdout=fp, stderr=fp).pid
			pid = run_ns_process_background(hostname, commands, output=log_fn)
		else:
			# /dev/null
			# pid = subprocess.Popen(commands.split(" "), stdout=DEVNULL, stderr=DEVNULL).pid
			pid = run_ns_process_background(hostname, commands)
		return pid, self.generator_id

	def _do_start_traffic_to_target(self, hid, target_id, flow_type) -> (int, int):
		hostname = "h{}".format(hid)
		intf = "{}-eth0".format(hostname)
		target_id_fn = os.path.join(target_id_dir, "{}.targetids".format(hostname))
		gen_id = self.generator_id
		self.generator_id += 1
		log_fn = "/tmp/{}.{}.gen.log".format(hostname, gen_id)
		pkt_dir = self.config["traffic_dir"][flow_type]
		ftype = -1
		report = False
		vlanid = -1
		if flow_type == "video":
			ftype = 0
			# report=True
			vlanid = 0
		elif flow_type == "iot":
			ftype = 1
			vlanid = 1
		elif flow_type == "voip":
			ftype = 2
			vlanid = 2
		elif flow_type == "ar":
			ftype = 3
			vlanid = 3
		else:
			raise Exception("Unsupported flow type")

		# report=True
		enable_loss = (int(self.config["enable_loss"]) == 1)

		base_dir = self.config["generator_log_dir"]
		loss_dir = os.path.join(base_dir, "{}.tx.loss".format(hid))

		controller_ip = self.config["controller"].split(":")[0]

		params = "--id {} " \
		         "--dst_id {} " \
		         "--pkts {} " \
		         "--mtu {} " \
		         "--int {} " \
		         "--cip {} " \
		         "--forcetarget " \
		         "--target {} " \
		         "--ftype {} " \
		         "--cport {} " \
		         "{} " \
		         "--loss_dir {} " \
		         "{} " \
		         "{} " \
				 "--stats " \
		         "--workers {}".format(
			hid,
			target_id_fn,
			pkt_dir,
			self.config["vhost_mtu"],
			intf,
			controller_ip,
			target_id,
			ftype,
			self.config["controller_socket_port"],
			("--loss" if enable_loss else ""),
			(loss_dir if enable_loss else ""),
			("--report" if report else ""),
			("{}".format("--vlan {}".format(vlanid) if not report else "")),
			1,
		)

		commands = "{} {}".format(self.binary, params)
		enable_log = (int(self.config["enable_traffic_generator_log"]) == 1)
		if enable_log:
			# fp = open(log_fn, "w")
			# pid = subprocess.Popen(commands.split(" "), stdout=fp, stderr=fp).pid
			pid = run_ns_process_background(hostname, commands, output=log_fn)
		else:
			# /dev/null
			# pid = subprocess.Popen(commands.split(" "), stdout=DEVNULL, stderr=DEVNULL).pid
			pid = run_ns_process_background(hostname, commands)

		# pid = subprocess.Popen(commands.split(" "), stdout=DEVNULL, stderr=DEVNULL).pid
		return pid, self.generator_id

	def _start_traffic(self, hid, flow_type, to_schedule=False):
		pid, genid = self._do_start_traffic(hid, flow_type)
		self.pid2genid[pid] = genid
		self.genid2pid[genid] = pid
		self.processes[flow_type].append(pid)

		if to_schedule:
			self.schedule_record.append(pid)

	def _start_traffic_to_target(self, hid, target_id, flow_type, to_schedule=False):
		pid, genid = self._do_start_traffic_to_target(hid, target_id, flow_type)
		self.pid2genid[pid] = genid
		self.genid2pid[genid] = pid
		self.processes[flow_type].append(pid)

		if to_schedule:
			self.schedule_record.append(pid)

	def _start_traffic_to_target_list(self, hid, target_id_list, flow_type, to_schedule=False,
	                                  cnt_process=4):
		for target_id in target_id_list:
			for _ in range(cnt_process):
				self._start_traffic_to_target(hid, target_id, flow_type, to_schedule)

	def _stop_traffic(self, pid, flow_type, to_schedule=True):
		kill_pid(pid)
		genid = self.pid2genid[pid]
		del self.pid2genid[pid]
		del self.genid2pid[genid]
		self.processes[flow_type].remove(pid)
		if to_schedule:
			self.schedule_record.remove(pid)

	def start_anomaly_traffic(self):
		config: Dict = self.config["anomaly_traffic"]
		src_id = config["src"]
		if src_id not in self.hostids:
			debug("noting to do return")
			return
		dst_id = config["dst"]
		debug("anomaly traffic src {}".format(src_id))
		debug("anomaly traffic dst {}".format(dst_id))
		pid, _ = self._do_start_traffic_to_target(int(src_id), int(dst_id), "video")
		self.anomaly_traffic_pid = pid

	def stop_anomaly_traffic(self):
		if hasattr(self, "anomaly_traffic_pid"):
			debug("kill anomaly traffic pid")
			kill_pid(self.anomaly_traffic_pid)
			return
		debug("noting to do return")

	def act(self, mode: str):
		'''
		state machine:
		None-->small<--->large
		:param mode: "small","large"
		:return: None
		'''
		assert mode in ["small", "large", "medium"]
		if self.prev_mode == mode:
			debug("traffic actor:nothing todo return")
			return

		if self.prev_mode is None:
			if mode == "small":
				flow_types = self.flow_types
				for ft in flow_types:
					for _ in range(self.config["num_process"][ft][0]):
						for hid in self.hostids:
							self._start_traffic(hid, ft)
				# ref
				for hid in [18]:
					self._start_traffic_to_target_list(hid, [40, 62, 84], "video", False, 1)
				debug("started {} process to form small flow".format(self.generator_id))
				self.prev_mode = mode
				return
			elif mode == "large":
				# not implemented
				pass

		# small-->large
		if self.prev_mode == "small":
			if mode == "large":
				debug("current mode:{}".format(self.cnt % 3 + 1))
				if self.cnt % 3 == 0:
					for hid in [0, 2, 4]:
						if hid in self.hostids:
							self._start_traffic_to_target_list(hid,
							                                   [18, 20, 22, 24, 26, 28, 40, 42, 44,
							                                    46, 48, 50], "video", True)
					for hid in [6, 8, 10]:
						if hid in self.hostids:
							self._start_traffic_to_target_list(hid,
							                                   [62, 64, 66, 68, 70, 72, 84, 86, 88,
							                                    90, 92, 94], "video", True)

				if self.cnt % 3 == 1:
					for hid in [18, 19, 20]:
						if hid in self.hostids:
							self._start_traffic_to_target_list(hid, [40, 42, 44, 46, 48, 50],
							                                   "video", True)

				if self.cnt % 3 == 2:
					for hid in [18, 19, 20]:
						if hid in self.hostids:
							self._start_traffic_to_target_list(hid,
							                                   [33, 32, 31, 30, 29, 28, 27, 26],
							                                   "video", True, 6)

				self.cnt += 1
		# large--->small
		if self.prev_mode == "large":
			if mode == "small":
				to_be_killed = self.schedule_record[:]
				for pid in to_be_killed:
					self._stop_traffic(pid, "video", True)

		self.prev_mode = mode
		debug("traffic actor act done")
		debug("***********Now mode is {}***********".format(mode))

	def stop(self):
		for pid in self.pid2genid.keys():
			kill_pid(pid)

		# 保险起见
		os.system("for p in `pgrep '^gogen$'`;do kill $p;done")
		self.processes = {
			"iot": [],
			"video": [],
			"voip": [],
			# "ar":[],
			# "ar":[],
		}
		self.genid2pid = {}
		self.pid2genid = {}
		self.prev_mode = None
		self.generator_id = 0
		self.schedule_record = []
		self.cnt = 0
