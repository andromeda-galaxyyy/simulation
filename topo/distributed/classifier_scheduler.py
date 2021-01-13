from utils.log_utils import debug, info, err, warn
from utils.process_utils import run_ns_process_background,kill_pid
from typing import Dict, List, Tuple
from utils.file_utils import dir_exsit, del_dir, create_dir


class ClassifierScheduler:
	def __init__(self, config: Dict, hosts: List[int]):
		self.config = config
		self.hosts = hosts
		self.pids = []

	def _start_traffic(self, host: int, target: int, log: bool, log_fn: str):
		config = self.config["classifier_demo"]
		classifier_ip = config["classifier_ip"]
		classifier_port = config["classifier_port"]
		redis_ip = config["redis_ip"]
		redis_port = config["redis_port"]
		redis_db = config["redis_db"]
		intf = "h{}-eth0".format(host)
		pkts_dir = config["pkts_dir"]
		binary = config["binary_file"]
		command = "{} " \
		          "--pkts_dir {} " \
		          "--workers {} " \
		          "--clsip {} " \
		          "--clsport {} " \
		          "--intf {} " \
		          "--rip {} " \
		          "--rport {} " \
		          "--rdb {} " \
		          "--id {} " \
		          "--target {}".format(
			binary,
			pkts_dir,
			3,
			classifier_ip,
			classifier_port,
			intf,
			redis_ip,
			redis_port,
			redis_db,
			host,
			target
		)
		h="h{}".format(host)
		output=None if not log else log_fn
		p=run_ns_process_background(h,command,output)
		return p

	def start(self):
		config: Dict = self.config["classifier_demo"]
		log_to_file: bool = int(config["log"]) == 1
		if log_to_file:
			debug("log to file")
		log_dir: str = config["log_dir"]
		if dir_exsit(log_dir):
			del_dir(log_dir)
		create_dir(log_dir)
		hosts: List[int] = config["hosts"]
		targets = config["target"]
		for idx, host in enumerate(hosts):
			if host not in self.hosts: continue
			ts = targets[idx]
			debug("host {},target {}".format(host, ts))
			for t in ts:
				debug("start traffic from {} to {}".format(host, t))
				log_fn = "{}_{}.classifier_demo".format(host, t)
				pid=self._start_traffic(host, t, log_to_file, log_fn)
				self.pids.append(pid)

	def stop(self):
		debug("stop classifier demo")
		for p in self.pids:
			kill_pid(p)
		self.pids=[]
		debug("classifier demo stopped")
