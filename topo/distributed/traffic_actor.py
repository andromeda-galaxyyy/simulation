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

target_id_dir = os.path.join(get_prj_root(), "topo/distributed/targetids")


def run_ns_binary(ns: str, bin: str, params: str, log_fn: str = "/tmp/log.log"):
	os.system("ip netns exec {} nohup {} {} >{} 2>&1 &".format(
		ns, bin, params, log_fn))


def kill_pid(pid):
	os.system("kill {}".format(pid))


class TrafficActor:
	def __init__(self, config: Dict,hostids:List[int]):
		self.hostids = hostids
		self.prev_mode = None
		self.config = config

		self.generator_id = 0
		self.genid2pid = {}
		self.pid2genid = {}
		self.processes = {
			"iot": [],
			"video": [],
			"voip": []
		}
		self.flow_types = ["video", "iot", "voip"]
		self.binary = self.config["traffic_generator"]

		# self.traffic_scales = ["small", "small", "small", "small"]
		self.traffic_scales = self.config["traffic_mode"]
		self.durations = self.config["traffic_duration"]
		assert len(self.traffic_scales) == len(self.durations)
		# self.durations = [120, 120, 120, 120]
		self.flow_types = ["video", "iot", "voip"]

		self.schedule_record = []
		random.seed(int(time.time()))
		gen_base_log_dir = config["generator_log_dir"]
		del_dir(gen_base_log_dir)
		create_dir(gen_base_log_dir)

	def _do_start_traffic(self, hid, flow_type) -> (int, int):
		hostname = "h{}".format(hid)
		intf = "{}-eth0".format(hostname)
		target_id_fn = os.path.join(target_id_dir, "{}.targetids".format(hostname))
		gen_id = self.generator_id
		self.generator_id += 1
		log_fn = "/tmp/{}.{}.gen.log".format(hostname, gen_id)
		pkt_dir = self.config["traffic_dir"][flow_type]
		ftype = -1
		if flow_type == "video":
			ftype = 0
		elif flow_type == "iot":
			ftype = 1
		elif flow_type == "voip":
			ftype = 2
		else:
			raise Exception("Unsupported flow type")

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
		         "--loss_dir {}".format(
			hid,
			target_id_fn,
			pkt_dir,
			self.config["vhost_mtu"],
			intf,
			controller_ip,
			ftype,
			self.config["controller_socket_port"],
			("--loss" if enable_loss else ""),
			(loss_dir if enable_loss else "")
		)

		commands = "nohup ip netns exec {} {} {}".format(
			hostname, self.binary, params)

		enable_log = (int(self.config["enable_traffic_generator_log"]) == 1)
		if enable_log:
			fp = open(log_fn, "w")
			pid = subprocess.Popen(commands.split(" "), stdout=fp, stderr=fp).pid
		else:
			# /dev/null
			pid = subprocess.Popen(commands.split(
				" "), stdout=DEVNULL, stderr=DEVNULL).pid
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
		if flow_type == "video":
			ftype = 0
		elif flow_type == "iot":
			ftype = 1
		elif flow_type == "voip":
			ftype = 2
		else:
			raise Exception("Unsupported flow type")

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
		         "--loss_dir {}".format(
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
			(loss_dir if enable_loss else "")
		)

		commands = "nohup ip netns exec {} {} {}".format(
			hostname, self.binary, params)
		enable_log = (int(self.config["enable_traffic_generator_log"]) == 1)
		if enable_log:
			fp = open(log_fn, "w")
			pid = subprocess.Popen(commands.split(" "), stdout=fp, stderr=fp).pid
		else:
			# /dev/null
			pid = subprocess.Popen(commands.split(
				" "), stdout=DEVNULL, stderr=DEVNULL).pid

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

	def _stop_traffic(self, pid, flow_type, to_schedule=True):
		kill_pid(pid)
		genid = self.pid2genid[pid]
		del self.pid2genid[pid]
		del self.genid2pid[genid]
		self.processes[flow_type].remove(pid)
		if to_schedule:
			self.schedule_record.remove(pid)

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
				debug("started {} process to form small flow".format(self.generator_id))
				self.prev_mode=mode
				return
			elif mode == "large":
				# not implemented
				pass

		# small-->large
		target_n_host = None
		n_hosts = len(self.hostids)
		if self.prev_mode == "small":
			if mode == "large":
				target_n_host = math.ceil(n_hosts * 0.5)

		# large--->small
		if self.prev_mode == "large":
			if mode == "small":
				target_n_host = 0

		target_n_process = target_n_host * 15

		if target_n_process > len(self.schedule_record):
			n_add = target_n_process - len(self.schedule_record)
			# sample host
			# sampled_hosts = random.sample(self.hostids, n_add // 15)
			n_sampled = n_add // 15
			# 从start开始的某一段连续的主机,数量为n_sampled
			start = random.sample(range(len(self.hostids) - n_sampled), 1)[0]
			# debug("sampled host start from {}, number of hosts {}".format(start,n_sampled))
			sampled_hosts = self.hostids[start:start + n_sampled]
			for hid in sampled_hosts:
				for _ in range(15):
					self._start_traffic(hid, "video", True)

		# we need to reduce generator
		elif target_n_process < len(self.schedule_record):
			to_be_killed = self.schedule_record[target_n_process:]
			for pid in to_be_killed:
				self._stop_traffic(pid, "video", True)

		self.prev_mode = mode
		debug("traffic actor act done")

	def stop(self):
		for pid in self.pid2genid.keys():
			kill_pid(pid)

		# 保险起见
		os.system("for p in `pgrep '^gen$'`;do kill $p;done")
		self.processes = {
			"iot": [],
			"video": [],
			"voip": []
		}
		self.genid2pid = {}
		self.pid2genid = {}
