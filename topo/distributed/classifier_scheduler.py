from utils.log_utils import debug, info, err, warn
from utils.process_utils import run_ns_process_background, kill_pid
from typing import Dict, List, Tuple
from utils.file_utils import dir_exsit, del_dir, create_dir
import os


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
		h = "h{}".format(host)
		output = None if not log else log_fn
		p = run_ns_process_background(h, command, output)
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
				pid = self._start_traffic(host, t, log_to_file, log_fn)
				self.pids.append(pid)

	def stop(self):
		debug("stop classifier demo")
		for p in self.pids:
			kill_pid(p)
		self.pids = []
		debug("classifier demo stopped")


from path_utils import get_prj_root

target_id_dir = os.path.join(get_prj_root(), "topo/distributed/targetids")


# with controller
class ClassifierScheduler2:
	def __init__(self, config: Dict, hosts: List[int]):
		self.config = config
		self.hosts = hosts
		self.pids = []

	def _start_traffic(self, host: int, target: int, log: bool, log_fn: str, flow_type="video"):
		config = self.config["classifier_demo"]
		if flow_type not in ["iot", "video", "voip", "ar"]:
			err("invalid flow type {}".format(flow_type))
			return -1
		pkts_dir = config[flow_type]

		target_id = target
		hid = host
		hostname = "h{}".format(hid)
		intf = "{}-eth0".format(hostname)
		target_id_fn = os.path.join(target_id_dir, "{}.targetids".format(hostname))
		# pkt_dir = self.config["traffic_dir"][flow_type]
		ftype = -1
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
		report = True

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
		         "--workers {}".format(
			hid,
			target_id_fn,
			pkts_dir,
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

		binary = self.config["traffic_generator"]
		commands = "{} {}".format(binary, params)
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
		return pid

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
				pid = self._start_traffic(host, t, log_to_file, log_fn)
				self.pids.append(pid)

	def stop(self):
		debug("stop classifier demo")
		for p in self.pids:
			kill_pid(p)
		self.pids = []
		debug("classifier demo stopped")
