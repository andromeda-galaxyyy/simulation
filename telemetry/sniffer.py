from argparse import PARSER
from itertools import count
from time import sleep

from utils.process_utils import start_new_thread_and_run
from scapy.all import *
from utils.time_utils import now_in_milli

from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether, Dot1Q

from scapy import config
from telemetry.base_telemeter import BaseTelemeter
from typing import Tuple, List, Dict
from scapy.all import *
from utils.log_utils import debug, info, err
import threading
import argparse
from utils.file_utils import load_json
from path_utils import get_prj_root
from utils.file_utils import load_pkl,save_pkl

paths = None
links=None


true_topo = None


class Sniffer:
	def __init__(self, count: int, intf: str, filter: str) -> None:
		self.pkt_count = count
		self.intf = intf
		self.filter = filter
		self.cache = []
		self.edge_port = {}

	def __load_topo(self):
		# link->port
		port = self.edge_port
		port_edges = []

		# with open('../../topoInfo/topo0.json', 'r') as f:
		#     topy = json.load(f)["0"]
		# print(topy)
		topy = load_json(os.path.join(
			get_prj_root(), "telemetry/topo0.json"))["0"]
		for links in topy:
			for k in links.keys():
				# print(k)
				temp = k.split("--->")
				link = (int(temp[0]) + 1, int(temp[1]) + 1)
				# print(link)
				port[link] = int(links[k])
		# print(port)
		# for (u, v) in port.keys():
		#     port[(u, v)] = (port[(u, v)], port[(v, u)])
		for (u, v) in port.keys():
			if (v, u) not in port_edges:
				port[(u, v)] = (port[(u, v)], port[(v, u)])
				port_edges.append((u, v))
		for (u, v) in port_edges:
			del port[(v, u)]
		port[(0, 23)] = (1, 1)
		# port[(0, self.monitor)] = (1, 1)
		# return port

	def __calculate_rtt(self):
		switch_msg = {}
		link_rtt = {}
		# switch_msg: ip->port->time
		for pkt in self.cache:
			t = pkt.time
			port = int(pkt[Dot1Q].vlan)
			src = str(pkt[IP].src)
			if src in switch_msg.keys():
				if port in switch_msg[src].keys():
					err("error, {} already in items".format(port))
					return
				switch_msg[src][port] = t
			else:
				temp = {}
				temp[port] = t
				switch_msg[src] = temp

		for u, v in links:
			t1 = None
			t2 = None
			x, y, z = self.find_port(u, v)
			if (y, z) in self.edge_port.keys():
				if (x, y) in self.edge_port.keys():
					t1 = switch_msg["10.0.1.{}".format(z)][self.edge_port[(y, z)][1]]
					t2 = switch_msg["10.0.1.{}".format(y)][self.edge_port[(x, y)][1]]
				elif (y, x) in self.edge_port.keys():
					t1 = switch_msg["10.0.1.{}".format(z)][self.edge_port[(y, z)][1]]
					t2 = switch_msg["10.0.1.{}".format(y)][self.edge_port[(y, x)][0]]
				link_rtt[(u, v)] = abs(t1 - t2) * 1000
				# debug("link {}'s rtt => {}  ----  1 ".format((u, v), abs(t1 - t2) * 1000))
			elif (z, y) in self.edge_port.keys():
				if (x, y) in self.edge_port.keys():
					t1 = switch_msg["10.0.1.{}".format(z)][self.edge_port[(z, y)][0]]
					t2 = switch_msg["10.0.1.{}".format(y)][self.edge_port[(x, y)][1]]
				elif (y, x) in self.edge_port.keys():
					t1 = switch_msg["10.0.1.{}".format(z)][self.edge_port[(z, y)][0]]
					t2 = switch_msg["10.0.1.{}".format(y)][self.edge_port[(y, x)][0]]
				link_rtt[(u, v)] = abs(t1 - t2) * 1000
				# debug("link {}'s rtt => {} ".format((u, v), abs(t1 - t2) * 1000))
			else:
				err("error,{} has no port msg".format((u, v)))

		ma = -1
		for u, v in link_rtt.keys():
			true_delay = int(true_topo[u - 1][v - 1][1]) * 2
			ma = max(ma, abs(true_delay - link_rtt[(u, v)]) / true_delay)
		#fixed link stats
		fixed_link_stats={}
		for u,v in link_rtt.keys():
			fixed_link_stats[(u-1,v-1)]=link_rtt[(u,v)]
			fixed_link_stats[(v-1,u-1)]=link_rtt[(u,v)]
		save_pkl("/tmp/telemetry.link.pkl",fixed_link_stats)


	def find_port(self, u, v):
		for path in paths:
			for i in range(1, len(path) - 1):
				if path[i] == u and path[i + 1] == v:
					return path[i - 1], u, v
				elif path[i] == v and path[i + 1] == u:
					return path[i - 1], v, u

	def __send_telemetry_packet_and_listen(self) -> Tuple[int, str]:
		sniffer_lock = threading.Lock()
		current_count = 0
		sniffer_started = False
		send_time = -1

		def sniffer_started_cbk():
			nonlocal sniffer_lock
			sniffer_lock.acquire()
			nonlocal sniffer_started
			sniffer_started = True
			debug("AsyncSniffer started and lock acquired")

		def handle_pkt(pkt):
			self.cache.append(pkt)
			nonlocal current_count, send_time
			current_count += 1
			if current_count == self.pkt_count:
				debug("Received all pkts so far,release the lock")
				sniffer_lock.release()

		sniffer = AsyncSniffer(iface=self.intf, count=self.pkt_count, prn=handle_pkt,
		                       started_callback=sniffer_started_cbk, filter=self.filter)
		start_new_thread_and_run(func=sniffer.start, args=())

		# wait for sniffer start
		while not sniffer_started:
			sleep(0.1)
		# sniffer started,now send pkt
		debug("Sniffer started,now send pkt")
		p = Ether() / Dot1Q(vlan=3) / IP(src="10.0.0.1", dst="10.0.0.2") / \
		    UDP(dport=8888, sport=1500) / Raw(load="1234")
		sendp(p, iface=self.intf)
		debug("Telemetry pkt sent,now wait for all pkts received")
		sniffer_lock.acquire()
		debug("All returned pkts received")


		return 0, ""

	def start(self):
		self.__load_topo()
		self.__send_telemetry_packet_and_listen()
		self.__calculate_rtt()
		self.cache = []


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--intf", type=str, help="Interface to send and listen", default="h22-eth0")
	parser.add_argument("--filter", type=str,
	                    help="BPF filter", default="udp port 8888")
	parser.add_argument("--count", type=int,
	                    help="Number of packets to received", default=102)

	parser.add_argument("--links",
	                    type=str,
	                    help="Pickle file to store links",
	                    default=os.path.join(get_prj_root(),"telemetry/default_required_links.pkl"))

	parser.add_argument("--paths",
	                    type=str,
	                    help="JSON file to store paths information",
	                    default=os.path.join(get_prj_root(),"telemetry/default_paths.json")
	                    )

	parser.add_argument("--topo",
	                    type=str,
	                    help="Json file to store topo information",
	                    default=os.path.join(get_prj_root(),"telemetry/topo0.json"))

	args = parser.parse_args()
	sniffer = Sniffer(count=int(args.count),
	                  intf=args.intf, filter=args.filter)

	true_topo = load_pkl(os.path.join(get_prj_root(), "static/satellite_overall.pkl"))[0]["topo"]
	links=load_pkl(args.links)
	paths=load_json(args.paths)["paths"]
	sniffer.start()
