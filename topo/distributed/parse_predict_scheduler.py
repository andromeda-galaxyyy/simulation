from utils.log_utils import debug, info, err, warn
from utils.process_utils import run_ns_process_background, kill_pid
from typing import Dict, List, Tuple
from utils.file_utils import dir_exsit, del_dir, create_dir
import os

from path_utils import get_prj_root

target_id_dir = os.path.join(get_prj_root(), "topo/distributed/targetids")


# with controller
class PktsPrinter:
	def __init__(self, config: Dict, hosts: List[int]):
		self.config = config
		self.hosts = hosts
		self.pids = []

	def _start_traffic(self, host: int, target: int,ftype_="voip"):
		config = self.config["flow_prediction"]
		target_id = target
		hid = host
		hostname = "h{}".format(hid)
		intf = "{}-eth0".format(hostname)
		target_id_fn = os.path.join(target_id_dir, "{}.targetids".format(hostname))
		# pkt_dir = self.config["traffic_dir"][flow_type]
		ftype = 0
		vlanid = 5

		pkts_dir=config[ftype_]["pkts"]
		printer="/tmp/{}.prediction".format(ftype_)

		enable_loss = (int(self.config["enable_loss"]) == 1)
		base_dir = self.config["generator_log_dir"]
		loss_dir = os.path.join(base_dir, "{}.tx.loss".format(hid))

		controller_ip = self.config["controller"].split(":")[0]
		report = False
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
		         "--debug " \
		         "--loss_dir {} " \
		         "{} " \
		         "{} " \
				 "--printer {} "\
		         "--workers {}".format(
			hid,
			target_id_fn,
			pkts_dir,
			self.config["vhost_mtu"],
			intf,
			controller_ip,
			target_id,
			ftype,
			1050,
			("--loss" if enable_loss else ""),
			(loss_dir if enable_loss else ""),
			("--report" if report else ""),
			("{}".format("--vlan {}".format(vlanid) if not report else "")),
			printer,
			1,
		)

		binary = config["bin"]
		commands = "{} {}".format(binary, params)
		# enable_log = (int(self.config["enable_traffic_generator_log"]) == 1)
		enable_log = True
		if enable_log:
			# fp = open(log_fn, "w")
			# pid = subprocess.Popen(commands.split(" "), stdout=fp, stderr=fp).pid
			pid = run_ns_process_background(hostname, commands, "/tmp/predict.{}.log".format(ftype_))
		else:
			# /dev/null
			# pid = subprocess.Popen(commands.split(" "), stdout=DEVNULL, stderr=DEVNULL).pid
			pid = run_ns_process_background(hostname, commands)

		# pid = subprocess.Popen(commands.split(" "), stdout=DEVNULL, stderr=DEVNULL).pid
		return pid

	def start(self):
		config: Dict = self.config["flow_prediction"]
		src = config["src"]
		dst = config["dst"]
		if src not in self.hosts:
			debug("nothing to do,return")
			return
		for ftype in ["voip","iot","ar"]:
			pid = self._start_traffic(src, dst,ftype)
			self.pids.append(pid)

	def stop(self):
		debug("stop printer demo")
		os.system("pkill for_predict")
		for p in self.pids:
			kill_pid(p)
		self.pids = []
		debug("printer demo stopped")
