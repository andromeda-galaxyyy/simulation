from scapy.layers.inet import IP, UDP, TCP
from scapy.layers.l2 import Ether

from typing import List, Tuple
from scapy.all import *
from time import sleep
from argparse import ArgumentParser
from copy import deepcopy
import json


def generate_ip(id_):
	id_ = int(id_) + 1
	if 1 <= id_ <= 254:
		return "10.0.0." + str(id_)
	if 255 <= id_ <= 255 * 254 + 253:
		return "10.0." + str(id_ // 254) + "." + str(id_ % 254)
	raise Exception("Cannot support id address given a too large id")


def generate_mac(id_):
	id_ = int(id_) + 1

	def base_16(num):
		res = []
		num = int(num)
		if num == 0:
			return "0"
		while num > 0:
			left = num % 16
			res.append(left if left < 10 else chr(ord('a') + (left - 10)))
			num //= 16
		res.reverse()
		return "".join(map(str, res))

	raw_str = base_16(id_)
	if len(raw_str) > 12:
		raise Exception("Invalid id")
	# reverse
	raw_str = raw_str[::-1]
	to_complete = 12 - len(raw_str)
	while to_complete > 0:
		raw_str += "0"
		to_complete -= 1
	mac_addr = ":".join([raw_str[i:i + 2] for i in range(0, len(raw_str), 2)])
	mac_addr = mac_addr[::-1]
	return mac_addr


# def start_new_thread_and_run()
def send_msg(ip, port, msg):
	print("send msg")
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((ip, int(port)))
		s.sendall(bytes(json.dumps(msg), "ascii"))
		print("json :",json.dumps(msg))
		s.close()


def process_stats(ip, port, specifier: Tuple, pkt_size: List, idt: List):
	msg = {"specifier": specifier, "stats": []}
	msg["stats"].append(min(pkt_size))
	msg["stats"].append(max(pkt_size))
	msg["stats"].append(sum(pkt_size) / len(pkt_size))
	# todo std var
	msg["stats"].append(0)

	msg["stats"].append(min(idt))
	msg["stats"].append(max(idt))
	msg["stats"].append(sum(idt) / len(idt))
	msg["stats"].append(0)
	send_msg(ip, port, msg)


class Gen:
	def __init__(self, pkts_dir, self_id, dst_ids, win_size=5):
		# self.fn = pkts_fn
		self.pkts_dir = pkts_dir
		self.ip = generate_ip(self_id)
		self.id = self_id
		print("self ip {}".format(self.ip))
		self.dst_ips = [generate_ip(i) for i in dst_ids]
		self.mac = generate_mac(self_id)
		self.dst_macs = [generate_mac(i) for i in dst_ids]
		self.win_size = win_size

		# flow_stats[(specifier)]=={pkt_size:[],idt:[]}
		self.flow_stats = defaultdict(lambda: {"pkt_size": [], "idt": []})
		self.sent_record = set()

		self.specifier_to_flow_id = {}

	def reset(self):
		self.flow_stats = defaultdict(lambda: {"pkt_size": [], "idt": []})
		self.sent_record = set()
		self.specifier_to_flow_id = {}

	def __call__(self):
		pkt_files = list(os.listdir(self.pkts_dir))
		pkt_files = list(filter(lambda x: ".pkts" in x, pkt_files))
		if len(pkt_files) == 0:
			print("error: no pkt files")
			return
		pkt_file_idx = 0

		# 每个文件对应的端口段长度
		port_seg = (65535 - 1500) // len(pkt_files)

		while True:
			print("new loop")
			self.reset()
			fn = pkt_files[pkt_file_idx]
			fp = open(os.path.join(self.pkts_dir, fn), "r")
			pkts = fp.readlines()
			fp.close()

			n_dsts = len(self.dst_macs)
			one_byte = b'\xff'
			s = conf.L3socket(iface='h{}-eth0'.format(self.id))
			report_record = self.sent_record

			for pkt_line in pkts:
				to_sleep, size, proto, flow_id, ts_diff_in_flow = pkt_line.split(" ")
				size = int(size)

				flow_id = int(flow_id)
				# todo sleep
				to_sleep = float(to_sleep)
				ts_diff_in_flow = float(ts_diff_in_flow)

				dst_ip = self.dst_ips[flow_id % n_dsts]

				src_port = 1500 + (pkt_file_idx * port_seg) + flow_id % port_seg
				dst_port = src_port
				if proto == "TCP":
					l4 = TCP(sport=src_port, dport=dst_port) / (one_byte * size)
				else:
					l4 = UDP(sport=src_port, dport=dst_port) / (one_byte * size)

				pkt = IP(dst=dst_ip) / l4
				specifier = (src_port, dst_port, self.ip, dst_ip, proto)

				if flow_id not in report_record:
					# 统计信息
					self.flow_stats[specifier]["pkt_size"].append(size)
					if ts_diff_in_flow >= 0:
						self.flow_stats[specifier]["idt"].append(ts_diff_in_flow)
					if len(self.flow_stats[specifier]["pkt_size"]) == self.win_size:
						report_record.add(flow_id)
						thread = threading.Thread(target=process_stats,
						                          args=("192.168.64.1",
						                                "1026",
						                                deepcopy(specifier),
						                                deepcopy(
							                                self.flow_stats[specifier]["pkt_size"]),
						                                deepcopy(
							                                self.flow_stats[specifier]["idt"])))
						del self.flow_stats[specifier]
						thread.start()

				s.send(pkt)
				print("sent")
			pkt_file_idx = (pkt_file_idx + 1) % len(pkt_files)


if __name__ == '__main__':
	pkt_dir = "/home/ubuntu/temp/pkts"
	parser = ArgumentParser()
	parser.add_argument("--id", required=True, help="self id")
	parser.add_argument("--dst_id", required=True, help="destination id file")
	parser.add_argument("--pkts_dir", required=True, default=pkt_dir, help="pkts dir")
	args = parser.parse_args()
	with open(args.dst_id, "r") as fp:
		dst_ids = fp.readlines()
		fp.close()
	generator = Gen(args.pkts_dir, args.id, dst_ids)
	generator()
