from utils.file_utils import save_pkl
from utils.log_utils import debug, info, err
from typing import Any, List, Tuple, Dict
from sockets.client import send
import json
import time
import os
from path_utils import get_prj_root


class BaseTelemeter:
	def __init__(self, ovsids: List[int], topo: List[List[List[int]]], config: Dict) -> None:
		# 本服务器上的ovsid
		self.ovsids: List[int] = ovsids
		self.topo: List[List[List[int]]] = topo
		self.config: Dict = config
		self.sniffer_config = {
			"iface": "h22-eth0",
			"filter": "udp port 8888",
			"count": None,
			"namespace": "h22"
		}
		self.vars = {}
		self.not_self = False

	def _calculate_monitor(self, links: List[Tuple[int, int]]) -> Tuple[int, str, int]:
		raise NotImplementedError

	def _calculate_flow(self, links: List[Tuple[int, int]]) -> Tuple[int, str, Any]:
		'''
        抽象方法，由具体的子类给出实现方式,成功返回0，错误返回-1
        （错误码,出错信息,发送给控制器的内容,务必为json)
        '''
		# if anything goes wrong,
		# return -1,"error msg",{}
		# otherwise
		# return 0,"",{"flows":[]}
		raise NotImplementedError

	def _do_stop(self):
		raise NotImplementedError

	def _start_sniffer(self) -> Tuple[int, str]:
		'''
        send telemetry packet,return 0 if success,-1 otherwise
        str if any,indicates error message
        '''
		# if anything goes wrong,
		# return -1,"error msg"
		# otherwise
		# return 0,""
		raise NotImplementedError

	def _do_collect_stats(self) -> Tuple[int, str, Any]:
		'''
        collect link delay stats
        return 0 if success,-1 otherwise,str if any,indicates error message
       '''
		raise NotImplementedError

	def stop(self):
		if self.not_self:
			return
		debug("Stop telemeter")
		self._do_stop()

	def start(self, links: List[Tuple[int, int]]):
		# 计算monitor
		if links is None:
			links = [(38, 39), (4, 5), (62, 61), (28, 17), (61, 50), (2, 1), (36, 35), (29, 28),
			         (14, 15), (39, 40), (5, 6),
			         (54, 55), (44, 43), (43, 42), (52, 51), (61, 60), (29, 18), (12, 1), (44, 34),
			         (60, 49), (20, 19),
			         (37, 36), (30, 29), (3, 2), (13, 12), (46, 47), (22, 21), (53, 54), (23, 24),
			         (40, 41), (45, 46), (6, 7),
			         (24, 25), (60, 59), (51, 50), (59, 58), (30, 19), (13, 2), (38, 27), (38, 37),
			         (21, 20), (4, 3), (62, 63),
			         (7, 8), (50, 49), (39, 28), (44, 33), (14, 13), (31, 30), (52, 53), (18, 19),
			         (27, 28), (57, 56), (42, 41),
			         (64, 63), (12, 22), (35, 46), (55, 45), (66, 56), (34, 35), (10, 11), (58, 57),
			         (17, 16), (25, 26),
			         (1, 11), (63, 52), (18, 17), (27, 26), (9, 10), (27, 16), (45, 34), (62, 51),
			         (18, 7), (24, 13), (31, 32),
			         (57, 46), (47, 48), (24, 35), (40, 51), (6, 17), (19, 8), (15, 16), (56, 45),
			         (23, 33), (41, 52), (50, 39),
			         (32, 33), (55, 66), (29, 40), (11, 22), (12, 23), (55, 44), (49, 38), (30, 41),
			         (8, 9), (49, 48), (65, 64),
			         (34, 23), (66, 65), (33, 22), (16, 5)]

		ret_code, msg, monitor_id = self._calculate_monitor(links)
		monitor_id = int(monitor_id) - 1
		if ret_code != 0:
			err("Error when calculate monitor {}".format(msg))
			return
		# 如果monitor不在本服务器上,返回
		if monitor_id not in self.ovsids:
			self.not_self = True
			debug("Noting todo on this server,return")
			return
		vlan_to_link = {}
		link_to_vlan = {}
		num = 1
		for i in range(len(self.topo)):
			for j in range(len(self.topo[i])):
				if -1 in self.topo[i][j]:
					continue
				vlan_to_link[num] = (i + 1, j + 1)
				link_to_vlan[(i + 1, j + 1)] = num
				num += 1
		vlan_to_link[num] = (self.vars["monitor"], 0)
		link_to_vlan[(self.vars["monitor"], 0)] = num
		self.vars["vlan_to_link"] = vlan_to_link
		self.vars["link_to_vlan"] = link_to_vlan

		static_dir = os.path.join(get_prj_root(), "static")
		self.sniffer_config["link_to_vlan_fn"]=os.path.join(static_dir,"telemetry.link_to_vlan.pkl")
		save_pkl(os.path.join(static_dir, "telemetry.link_to_vlan.pkl"), link_to_vlan)

		debug("Monitory calculated")
		debug("Start to calculate flow rules")
		ret_code, msg, obj = self._calculate_flow(links)
		if ret_code != 0:
			err("Error when calculate flow,msg:{}".format(msg))
			return
		debug("Calculate flow successfully")
		# send to controller
		debug("Start to send to controller")
		controller_ip = self.config["controller"].split(":")[0]
		controller_telemetry_port = int(self.config["controller_telemetry_port"])
		send(controller_ip, controller_telemetry_port, json.dumps(obj) + "*")
		debug("Flow rules sent to controller")
		return
		# sleep for 10 seconds,wait for flow rules to be installed
		time.sleep(10)
		# send telemetry_packet and listen
		debug("Wake up from 10-seconds sleep")
		debug("Start to send telemetry packet")
		ret_code, msg = self._start_sniffer()
		if ret_code != 0:
			err("Error when send telemetry_packet and listen {}".format(msg))
			return

		debug("Waiting for telemetry done, for 10 seconds")
		time.sleep(10)
		debug("Telemetry work done")

	def collect_stats(self) -> Any:
		if self.not_self:
			return
		debug("Start to collect stats")
		ret_code, msg, obj = self._do_collect_stats()
		if ret_code != -1:
			err("Error when collect stats {}".format(msg))
			return

