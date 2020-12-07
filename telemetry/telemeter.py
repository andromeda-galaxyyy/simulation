from itertools import count
from os import kill
from time import process_time, sleep
from utils.process_utils import run_ns_process_background, run_process_background, \
	start_new_thread_and_run
from utils.process_utils import kill_pid
from path_utils import get_prj_root
from scapy import config
from telemetry.base_telemeter import BaseTelemeter
from typing import Tuple, List, Dict
from scapy.all import *
from utils.log_utils import debug, info, err
import threading
from typing import List, Any
from utils.file_utils import load_pkl
from utils.file_utils import load_json
from telemetry.base_telemeter import BaseTelemeter
from utils.log_utils import debug, info
import telemetry.calculate_monitor as cm
import telemetry.write_commands as wt
from utils.file_utils import save_json,load_json
from path_utils import get_prj_root
import os


class Telemeter(BaseTelemeter):
	def _start_sniffer(self) -> Tuple[int, str]:
		command = "python ./telemetry/sniffer.py --count {} --intf {} --filter '{}' --link_to_vlan " \
		          "'{}' --paths".format(
			self.sniffer_config["count"],
			self.sniffer_config["iface"],
			self.sniffer_config["filter"],
			self.sniffer_config["link_to_vlan_fn"],
			self.sniffer_config["paths"]
		)
		pid = run_ns_process_background(ns=self.sniffer_config["namespace"], command=command,
		                                output="/tmp/sniffer.log")
		self.sniffer_pid = pid
		debug("started subprocess pid {}".format(pid))
		return 0, ""

	def _do_stop(self):
		if hasattr(self, "sniffer_pid"):
			kill_pid(self.sniffer_pid)

	def _calculate_monitor(self, links: List[Tuple[int, int]]) -> Tuple[int, str, int]:
		g = cm.makeTopo(self.topo)
		# self.vars["edge_port"]=edge_port
		debug("拓扑节点集：{}".format(g.nodes))
		debug("拓扑边集：{}".format(g.edges))
		# print(type(g.edges))
		location = cm.Biding(links, g)
		result = location.biding_strategy()
		if result[0] == -1:
			return result
		elif result[0] == 0:
			self.vars["monitor"] = result[1]
			self.vars["paths"] = result[2]
			paths_fn=os.path.join(get_prj_root(),"static/telemetry.paths.json")
			save_json(paths_fn,{"paths":result[2]})
			self.vars["recv_num"] = result[3]
			self.sniffer_config["count"] = result[3]
			self.sniffer_config["paths"] = result[2]
			return 0, "", self.vars["monitor"]

	def _calculate_flow(self, links: List[Tuple[int, int]]) -> Tuple[int, str, Any]:
		switches = 66
		t = wt.table(links, self.vars["paths"], switches, self.vars["monitor"],
		             self.vars["link_to_vlan"])
		flow_table = t.make_res()
		return 0, "", flow_table

	def _do_collect_stats(self) -> Tuple[int, str, Any]:
		return 0, "", load_pkl("/tmp/telemetry.link.pkl")
