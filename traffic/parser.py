import os
import pathlib
import dpkt
import socket
from typing import Mapping, Dict, Tuple, List
from collections import defaultdict

import shutil
from utils.common_utils import save_json, debug, info, check_file, check_dir
from os import listdir
from collections import Counter


def mac_addr(address):
	"""Convert a MAC address to a readable/printable string

	   Args:
		   address (str): a MAC address in hex form (e.g. '\x01\x02\x03\x04\x05\x06')
	   Returns:
		   str: Printable/readable MAC address
	"""
	return ':'.join('%02x' % ord(b) for b in address)


def inet_to_str(inet):
	"""Convert inet object to a string

		Args:
			inet (inet struct): inet network address
		Returns:
			str: Printable/readable IP address
	"""
	# First try ipv4 and then ipv6
	try:
		return socket.inet_ntop(socket.AF_INET, inet)
	except ValueError:
		return socket.inet_ntop(socket.AF_INET6, inet)


class Parser:
	def __init__(self, pcap_file: str, proto="TCP"):
		check_file(pcap_file)
		self.file = pcap_file
		self.proto = proto

	def parse(self) -> Dict[Tuple, List[Tuple]]:
		proto = None
		res = defaultdict(lambda: [])
		if self.proto == "TCP":
			proto = dpkt.ip.IP_PROTO_TCP
		else:
			proto = dpkt.ip.IP_PROTO_UDP
		fp = open(self.file, 'rb')
		pcap = list(dpkt.pcap.Reader(fp))
		for ts, buf in pcap:
			try:
				eth = dpkt.ethernet.Ethernet(buf)
			except Exception as e:
				continue
			if eth.type != dpkt.ethernet.ETH_TYPE_IP:
				continue

			ip = eth.data
			if not hasattr(ip, "p"): continue
			if ip.p != proto:
				continue
			sip = inet_to_str(ip.src)
			dip = inet_to_str(ip.dst)
			l4 = ip.data
			sport = l4.sport
			dport = l4.dport
			res[(sip, sport, dip, dport, self.proto)].append((ts, l4))
		return res


class TCPParser(Parser):
	def __init__(self, pcap_file: str):
		super(TCPParser, self).__init__(pcap_file, "TCP")

	def parse(self) -> Dict[Tuple, List[Tuple]]:

		packets = super(TCPParser, self).parse()

		for key in packets.keys():
			packets[key] = [(ts, len(x.data)) for ts, x in packets[key]]

		# packet (timestamp,l4 data size)

		debug("There is {} flows (maybe bidirectional)".format(len(packets)))
		res: Dict[Tuple, List[Tuple]] = defaultdict(list)

		for specifier in list(packets.keys()):

			sip = specifier[0]
			sport = specifier[1]
			dip = specifier[2]
			dport = specifier[3]

			reverse_specifier = (dip, dport, sip, sport, "TCP")
			if specifier in list(res.keys()) or reverse_specifier in list(res.keys()):
				continue

			pkt_size = [p[1] for p in packets[specifier]]

			flow_size = sum(pkt_size)
			reverse_pkt_size = [p[1] for p in packets[reverse_specifier]]
			reverse_flow_size = sum(reverse_pkt_size)

			flow_specifier = None
			if flow_size > reverse_flow_size:
				flow_specifier = specifier
			else:
				flow_specifier = reverse_specifier

			res[flow_specifier] = packets[flow_specifier]
		info("There is {} disctinct flows".format(len(res)))

		return res


# todo make timestamp start from zero


def generate_ditg_files(flows: Dict[Tuple, List[Tuple]], dirname, statistics: Dict):
	counter = 0
	for specifier in list(flows.keys()):
		sip = specifier[0]
		sport = specifier[1]
		dip = specifier[2]
		dport = specifier[3]
		proto = specifier[4]
		key = "{}_{}_{}_{}_{}".format(sip, sport, dip, dport, proto)
		# diff time
		timestamps = [pkt[0] for pkt in flows[specifier]]
		if len(timestamps) == 0:
			continue
		pkt_size = [pkt[1] for pkt in flows[specifier]]
		flow_size = sum(pkt_size)

		flow = {}
		flow["num_pkt"] = len(pkt_size)

		# if len(pkt_size)<200:
		# 	continue

		flow["proto"] = proto
		flow["size"] = flow_size

		diff_ts = []
		pre_ts = timestamps[0]
		for ts in timestamps:
			# in pcap files, timestamp in in epoch time in seconds
			diff = (int(int((ts - pre_ts) * 1000000) / 1000) + 0.01)
			diff /= 3
			diff_ts.append(diff)
			pre_ts = ts
		idts_file = os.path.join(dirname, "{}.idts".format(key))
		ps_file = os.path.join(dirname, "{}.ps".format(key))
		flow["idt"] = "{}.idts".format(key)
		flow["ps"] = "{}.ps".format(key)
		with open(idts_file, 'a') as fp:
			for ts in diff_ts:
				fp.write("{}\n".format(ts))
			fp.flush()
			fp.close()
		# logger.debug("idts file written done")
		with open(ps_file, 'a') as fp:
			for ps in pkt_size:
				fp.write("{}\n".format(ps))
			fp.flush()
			fp.close()
		# logger.debug("ps file written done")
		statistics["flows"].append(flow)
		statistics["count"] += 1
	# print(sum(diff_ts))
	debug(counter)


# res_file=os.path.join(dirname,"statistics.json")


class UDPParser(Parser):
	def __init__(self, pcap_file: str):
		super(UDPParser, self).__init__(pcap_file, "UDP")

	def parse(self) -> Dict[Tuple, List[Tuple]]:
		packets = super(UDPParser, self).parse()

		for key in packets.keys():
			packets[key] = [(ts, len(x.data)) for ts, x in packets[key]]

		# packet (timestamp,l4 data size)

		debug("There is {} flows (maybe bidirectional)".format(len(packets)))
		res: Dict[Tuple, List[Tuple]] = defaultdict(list)

		for specifier in list(packets.keys()):

			sip = specifier[0]
			sport = specifier[1]
			dip = specifier[2]
			dport = specifier[3]

			reverse_specifier = (dip, dport, sip, sport, "UDP")
			if specifier in list(res.keys()) or reverse_specifier in list(res.keys()):
				continue

			pkt_size = [p[1] for p in packets[specifier]]

			flow_size = sum(pkt_size)
			reverse_pkt_size = [p[1] for p in packets[reverse_specifier]]
			reverse_flow_size = sum(reverse_pkt_size)

			flow_specifier = None
			if flow_size > reverse_flow_size:
				flow_specifier = specifier
			else:
				flow_specifier = reverse_specifier

			res[flow_specifier] = packets[flow_specifier]
		info("There is {} disctinct flows".format(len(res)))

		return res


if __name__ == '__main__':
	if pathlib.Path("/tmp/ditgs").is_dir():
		shutil.rmtree("/tmp/ditgs", ignore_errors=True)

	os.mkdir("/tmp/ditgs")

	files = [f for f in listdir("/tmp/pcaps") if 'pcap' in f]
	files = [os.path.join("/tmp/pcaps", f) for f in files]
	# files=["/tmp/pcaps/16-09-28.pcap"]
	statistics = {"count": 0, "flows": []}
	for file in files:
		debug("Parsing {}".format(file))
		p = TCPParser(file)
		res = p.parse()
		for f in list(res.keys()):
			res[f] = list(filter(lambda x: x[1] != 0, res[f]))

		generate_ditg_files(res, "/tmp/ditgs", statistics)

	save_json("/tmp/ditgs/statistics.json", statistics)
# filter zero size packets
