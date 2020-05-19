import os
import pathlib
import dpkt
import socket
from typing import Mapping, Dict, Tuple, List
from collections import defaultdict

import shutil
from utils.common_utils import save_json, debug, info, check_file, check_dir, dir_exsit
from os import listdir
from collections import Counter
from argparse import ArgumentParser

import socket


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
	def __init__(self, pcap_file: str, out_fn:str):
		check_file(pcap_file)
		self.file = pcap_file
		# if dir_exsit(out_dir):
		# 	os.rmdir(out_dir)
		# os.mkdir(out_dir)
		self.out_fn=out_fn

	def parse(self):
		fp = open(self.file, 'rb')
		raw_pkts = []
		pcap = list(dpkt.pcap.Reader(fp))
		tcp_proto = dpkt.ip.IP_PROTO_TCP
		udp_proto = dpkt.ip.IP_PROTO_UDP
		last_ts_in_flow = {}

		flow_idx = 1
		flow_sizes = defaultdict(lambda: 0)
		# 删除反向的流
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
			proto = ip.p
			specifier = (sip, sport, dip, dport, proto)
			flow_sizes[specifier] + len(l4.data)
			raw_pkts.append((specifier, (ts, len(l4.data))))

		# flow_id
		filtered_flow = {}

		# 查找业务流
		keys = list(flow_sizes)
		debug("#bidiretional flows: {}".format(len(keys)))
		for specifier in keys:
			sip = specifier[0]
			sport = specifier[1]
			dip = specifier[2]
			dport = specifier[3]
			proto = specifier[4]

			reverse_specifier = (dip, dport, sip, sport, proto)
			if specifier in filtered_flow or reverse_specifier in filtered_flow:
				continue

			flow_size = flow_sizes[specifier]
			reverse_flow_size = flow_sizes[reverse_specifier]

			if flow_size >= reverse_flow_size:
				flow_specifier = specifier
			else:
				flow_specifier = reverse_specifier

			filtered_flow[flow_specifier] = flow_idx
			flow_idx += 1
		debug("#flows {}".format(len(filtered_flow)))

		print(len(raw_pkts))
		raw_pkts = list(filter(lambda x: x[0] in filtered_flow, raw_pkts))
		debug("#raw valid pkts {}".format(len(raw_pkts)))

		timestamps = [pkt[1][0] for pkt in raw_pkts]
		time_diffs = [y - x for x, y in zip(timestamps, timestamps[1:])]
		with open(self.out_fn, 'w') as fp:
			for idx, pkt in enumerate(raw_pkts):
				# pkt =(specifier,(ts,size))
				specifier=pkt[0]

				flow_id = filtered_flow[specifier]
				if flow_id in last_ts_in_flow:
					diff_two_pkt = timestamps[idx] - last_ts_in_flow[flow_id]
				else:
					diff_two_pkt = -1

				last_ts_in_flow[flow_id] = timestamps[idx]

				specifier = pkt[0]
				if specifier[-1] == tcp_proto:
					proto = "TCP"
				else:
					proto = "UDP"
				if idx == len(raw_pkts) - 1:
					ts_diff = -1
				else:
					ts_diff = time_diffs[idx]

				size = pkt[1][1]
				fp.write("{} {} {} {} {}\n".format(ts_diff, size, proto, flow_id, diff_two_pkt))
			fp.flush()
			fp.close()


if __name__ == '__main__':
	for file in os.listdir("/Volumes/DATA/dataset/converted_iot"):
		if ".pcap" not in file:continue
		fn=os.path.join("/Volumes/DATA/dataset/converted_iot",file)
		fname=file[:-5]
		parser = Parser(fn, os.path.join("/tmp/pkts",fname+".pkts"))
		parser.parse()
