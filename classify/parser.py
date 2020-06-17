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
from argparse import ArgumentParser


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
	def __init__(self, pcap_file: str):
		check_file(pcap_file)
		self.file = pcap_file

	def parse(self):
		tcp_packets = defaultdict(lambda: [])
		udp_packets = defaultdict(lambda: [])

		tcp_proto = dpkt.ip.IP_PROTO_TCP
		udp_proto = dpkt.ip.IP_PROTO_UDP

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
			if ip.p != udp_proto and ip.p != tcp_proto:
				continue

			sip = inet_to_str(ip.src)
			dip = inet_to_str(ip.dst)
			l4 = ip.data
			if not hasattr(l4, "sport"): continue
			if not hasattr(l4, "dport"): continue
			sport = l4.sport
			dport = l4.dport

			# drop dns
			if dport == 53 or sport == 53:
				continue
			# drop dhcp
			if sport == 68 or dport == 68:
				continue
			if dport == 67 or sport == 67:
				continue
			# drop dns
			if ip.p == tcp_proto:
				tcp_packets[(sip, sport, dip, dport, "TCP")].append((ts, l4))
			elif ip.p == udp_proto:
				udp_packets[(sip, sport, dip, dport, "UDP")].append((ts, l4))
		return tcp_packets, udp_packets


class FilteredParser(Parser):
	def __init__(self, pcap_file: str):
		super(FilteredParser, self).__init__(pcap_file)
		self.fn = pcap_file
		debug("parsing {}".format(self.fn.split("/")[-1]))

	@staticmethod
	def _filter(packets: Dict):

		for key in packets.keys():
			packets[key] = [(ts, len(x.data)) for ts, x in packets[key] if len(x.data) > 0]

		# packet [(timestamp,l4_data_size)]

		debug("#{} flows (maybe bidirectional)".format(len(packets)))
		res: Dict[Tuple, List[Tuple]] = defaultdict(list)

		for specifier in packets.keys():

			sip = specifier[0]
			sport = specifier[1]
			dip = specifier[2]
			dport = specifier[3]
			proto = specifier[4]

			reverse_specifier = (dip, dport, sip, sport, proto)
			# 分析过了，掠过
			if specifier in res or reverse_specifier in res:
				continue

			pkt_size = [p[1] for p in packets[specifier]]

			flow_size = sum(pkt_size)
			reverse_pkt_size = [p[1] for p in packets[reverse_specifier]]
			reverse_flow_size = sum(reverse_pkt_size)

			if flow_size >= reverse_flow_size:
				flow_specifier = specifier
			else:
				flow_specifier = reverse_specifier

			res[flow_specifier] = packets[flow_specifier]
		info("There is {} distinct flows".format(len(res)))
		return res

	def parse(self):
		tcp_packets, udp_packets = super(FilteredParser, self).parse()
		tcp_packets = self._filter(tcp_packets)
		udp_packets = self._filter(udp_packets)
		return tcp_packets, udp_packets


# todo make timestamp start from zero

def generate_files(flows: Dict[Tuple, List[Tuple]], dirname, statistics: Dict, pcap_fn: str,
                   flow_type):
	for specifier in flows.keys():
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
		flow["file"] = pcap_fn.split("/")[-1]
		flow["duration"] = timestamps[-1] - timestamps[0]
		flow["type"] = flow_type

		diff_ts = []
		pre_ts = timestamps[0]
		for ts in timestamps:
			# diff = (int(int((ts - pre_ts) * 1000000) / 1000) + 0.01)
			if ts == pre_ts:
				diff = -1
			else:
				diff = (ts - pre_ts) * 1e9
			diff_ts.append(diff)
			pre_ts = ts

		idts_file = os.path.join(dirname, "{}.idts".format(key))
		ps_file = os.path.join(dirname, "{}.ps".format(key))
		flow["idt"] = "{}.idts".format(key)
		flow["ps"] = "{}.ps".format(key)
		with open(idts_file, 'w') as fp:
			for ts in diff_ts:
				fp.write("{}\n".format(ts))
			fp.flush()
			fp.close()
		# logger.debug("idts file written done")
		with open(ps_file, 'w') as fp:
			for ps in pkt_size:
				fp.write("{}\n".format(ps))
			fp.flush()
			fp.close()
		statistics["flows"].append(flow)
		statistics["count"] += 1


if __name__ == '__main__':
	pcaps_fn={
		"iot":["/Volumes/DATA/dataset/converted_iot","/tmp/dt/iot","iot"],
		"video":["/Volumes/DATA/dataset/cicdataset/video","/tmp/dt/video","video"],
		# "voip":[],
	}
	# parser = ArgumentParser()
	# parser.add_argument("--pcaps", help="Directory where pcap files stay", default="/tmp/pcaps",
	#                     type=str)
	# parser.add_argument("--output", help="Directory where ditg script stay", default="/tmp/ditgs",
	#                     type=str)
	# parser.add_argument("--ftype", help="Flow type", required=True)

	# args = parser.parse_args()
	for ftype in pcaps_fn.keys():
		pcaps_dir,output_dir,ftype=pcaps_fn[ftype]

		debug("remove ditg dir")
		if pathlib.Path(output_dir).is_dir():
			shutil.rmtree(output_dir, ignore_errors=True)

		os.mkdir(output_dir)

		files = [f for f in listdir(pcaps_dir) if 'pcap' in f]
		files = [os.path.join(pcaps_dir, f) for f in files]

		statistics = {"count": 0, "flows": []}
		for file in files:
			try:
				p = FilteredParser(file)
				tcp, udp = p.parse()
				for f in list(tcp.keys()):
				# remove tcp handshake and other packet in which data len=0
					tcp[f] = list(filter(lambda x: x[1] != 0, tcp[f]))
				for f in list(udp.keys()):
					udp[f] = list(filter(lambda x: x[1] != 0, udp[f]))
			except:
				continue

			generate_files(tcp, output_dir, statistics, file, ftype)
			generate_files(udp, output_dir, statistics, file, ftype)

		save_json(os.path.join(output_dir, "statistics.json"), statistics)
