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
	def __init__(self, pcap_file: str, out_fn: str, limit=True):
		check_file(pcap_file)
		self.file = pcap_file
		# if dir_exsit(out_dir):
		# 	os.rmdir(out_dir)
		# os.mkdir(out_dir)
		self.out_fn = out_fn
		self.limit = limit

	def parse(self,stats):
		fp = open(self.file, 'rb')
		raw_pkts = []
		pcap = list(dpkt.pcap.Reader(fp))
		tcp_proto = dpkt.ip.IP_PROTO_TCP
		udp_proto = dpkt.ip.IP_PROTO_UDP
		last_ts_in_flow = {}

		flow_idx = 0
		flow_sizes = defaultdict(lambda: 0)
		num_pkts = defaultdict(lambda: 0)

		for ts, buf in pcap:
			try:
				eth = dpkt.ethernet.Ethernet(buf)
			except Exception as e:
				continue
			if eth.type != dpkt.ethernet.ETH_TYPE_IP:
				continue

			ip = eth.data
			if not hasattr(ip, "p"):
				continue
			if ip.p != udp_proto and ip.p != tcp_proto:
				continue

			sip = inet_to_str(ip.src)
			dip = inet_to_str(ip.dst)
			l4 = ip.data
			if not hasattr(l4, "sport"):
				continue
			if not hasattr(l4, "dport"):
				continue

			sport = l4.sport
			dport = l4.dport
			# drop dhcp and dns packet
			if dport == 53: continue
			if sport == 53: continue
			if sport == 68: continue
			if dport == 67: continue

			proto = ip.p
			specifier = (sip, sport, dip, dport, proto)
			if len(l4.data) == 0:
				continue
			flow_sizes[specifier] += len(l4.data)
			num_pkts[specifier] += 1
			raw_pkts.append((specifier, (ts, len(l4.data))))

		# flow_id
		filtered_flow = {}
		# ratio=0.01 if self.limit else 1
		ratio = 1
		# 取前百分之10
		selected_specifiers = [s for s, num in sorted(num_pkts.items(), key=lambda item: -item[1])]
		# debug(selected_specifiers[0])
		selected_specifiers = selected_specifiers[:int(len(selected_specifiers) * ratio)]
		# selected_specifiers = [s for s in selected_specifiers if num_pkts[s] >= 5]

		debug("#selected specifier {}".format(len(selected_specifiers)))
		# 查找业务流
		keys = list(flow_sizes.keys())
		debug("#bidiretional flows: {}".format(len(keys)))

		for specifier in selected_specifiers:
			# if specifier not in selected_specifiers:
			# 	continue
			sip = specifier[0]
			sport = specifier[1]
			dip = specifier[2]
			dport = specifier[3]
			proto = specifier[4]

			reverse_specifier = (dip, dport, sip, sport, proto)
			if specifier in filtered_flow or reverse_specifier in filtered_flow:
				continue

			flow_size = 0
			reverse_flow_size = 0
			if specifier in flow_sizes:
				flow_size = flow_sizes[specifier]
			if reverse_specifier in flow_sizes:
				reverse_flow_size = flow_sizes[reverse_specifier]

			if flow_size == 0 and reverse_flow_size == 0:
				continue
			if flow_size >= reverse_flow_size:
				flow_specifier = specifier
			else:
				flow_specifier = reverse_specifier

			filtered_flow[flow_specifier] = flow_idx
			flow_idx += 1
		debug("#flows {}".format(len(filtered_flow)))

		# debug("#raw valid pkts {}".format(len(raw_pkts)))
		# pkt (specifier,(ts,size))
		raw_pkts = list(filter(lambda x: x[0] in filtered_flow, raw_pkts))

		raw_pkts = list(filter(lambda pkt: pkt[1][1] != 0, raw_pkts))

		pkt_sizes=[pkt[1][1] for pkt in raw_pkts]
		all_size=sum(pkt_sizes)


		# in nano seconds
		timestamps = [(pkt[1][0]) * 1e9 for pkt in raw_pkts]
		duration= (timestamps[-1]-timestamps[0]) / 1e9
		time_diffs = [y - x for x, y in zip(timestamps, timestamps[1:])]
		# set
		recorded_pkts = defaultdict(lambda: 0)

		#
		pcap_stats={
			"duration":0,
			"size":0,
		}
		with open(self.out_fn, 'w') as fp:
			for idx, pkt in enumerate(raw_pkts):
				# pkt =(specifier,(ts,size))
				specifier = pkt[0]
				if num_pkts[specifier] < 20:
					continue
				recorded_pkts[specifier] += 1

				flow_id = filtered_flow[specifier]
				# 跟同一个流中 上一个包的时间差
				if flow_id in last_ts_in_flow:
					diff_two_pkt_in_same_flow = timestamps[idx] - last_ts_in_flow[flow_id]
				else:
					diff_two_pkt_in_same_flow = -1

				last_ts_in_flow[flow_id] = timestamps[idx]

				specifier = pkt[0]
				if specifier[-1] == tcp_proto:
					proto = "TCP"
				else:
					proto = "UDP"
				# 距离下一个包的时间
				if idx == len(raw_pkts) - 1:
					ts_diff = -1
				else:
					ts_diff = time_diffs[idx]

				size = pkt[1][1]
				# finished=(recorded_pkts[specifier]==num_pkts[specifier])
				if recorded_pkts[specifier] == num_pkts[specifier]:
					finished = 1
				else:
					finished = 0
				fp.write("{} {} {} {} {} {}\n".format(ts_diff, size, proto, flow_id,
				                                      diff_two_pkt_in_same_flow, finished))
			fp.flush()
			fp.close()
		pcap_stats["duration"]=duration
		pcap_stats["size"]=all_size
		stats["pcaps"].append(pcap_stats)


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("--limit", dest="limit", action="store_true")
	args = parser.parse_args()
	pcaps_fns={
		# "iot":["/Volumes/DATA/dataset/converted_iot","/tmp/pkts/iot"],
		# "video":["/Volumes/DATA/dataset/cicdataset/video","/tmp/pkts/video"]
		"voip":["/Volumes/DATA/dataset/voip","/tmp/pkts/voip"]
	}

	for flow_type in pcaps_fns.keys():
		statistics = {"count": 0, "pcaps": []}
		pcaps,output=pcaps_fns[flow_type]
		shutil.rmtree(output, ignore_errors=True)
		os.mkdir(output)
		for file in os.listdir(pcaps):
			if ".pcap" not in file: continue
			fn = os.path.join(pcaps, file)
			fname = file[:-5]
			try:
				debug("start parsing {}".format(fname))
				parser = Parser(fn, os.path.join(output, fname + ".pkts"), limit=args.limit)
				parser.parse(statistics)
			except:
				continue
		save_json(os.path.join(output,"statistics.json"),statistics)
