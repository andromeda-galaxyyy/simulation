import random
import os
import subprocess
from multiprocessing import Process
from threading import Thread
from collections import defaultdict
import argparse
from time import sleep



def generate_ip(id):
	id = int(id) + 1
	if 1 <= id <= 254:
		return "10.0.0." + str(id)
	if 255 <= id <= 255 * 254 + 253:
		return "10.0." + str(id // 254) + "." + str(id % 254)
	raise Exception("Cannot support id address given a too large id")


def run(commands):
	return subprocess.run(commands)


def start_new_process_and_run(commands):
	p = Process(target=run, args=[commands])
	p.start()


class DummyGen:
	def __init__(self, lambada, self_id, dest_ids, n_ids):
		self.lambada = lambada
		self.id = self_id
		self.sig_ports = [1030,1031,1032,1033,1034]
		self.dest_ids = dest_ids
		self.offset = defaultdict(lambda: [0, 0])
		self.n_ids = n_ids
		self.sig_port_idx = defaultdict(lambda: 0)

	def start(self):
		seg_len = (65535 - 1500) // 2 // self.n_ids
		itg_script_fn = os.path.join("/tmp", "{}.itg.scripts".format(self.id))

		while True:
			# n_flows = np.random.poisson(self.lambada)
			n_flows=self.lambada
			if n_flows > 400:
				continue
			with open(itg_script_fn, 'w') as fp:
				for i in range(n_flows):
					dst_id = random.choice(self.dest_ids)
					dst_ip = generate_ip(dst_id)
					src_offset = self.offset[dst_id][0]
					dst_offset = self.offset[dst_id][1]
					# 1500-32017
					src_port_seg = list(
						range(1500 + dst_id * seg_len, 1500 + (dst_id + 1) * seg_len))
					# 32018-65535
					dst_port_seg = list(
						range(32018 + dst_id * seg_len, 32018 + (dst_id + 1) * seg_len))

					src_port = src_port_seg[src_offset]
					dst_port = dst_port_seg[dst_offset]
					self.offset[dst_id][0] = (self.offset[dst_id][0] + 1) % seg_len
					self.offset[dst_id][1] = (self.offset[dst_id][1] + 1) % seg_len

					# sig_port = self.sig_ports[self.sig_port_idx[dst_id]]
					sig_port=random.choice(self.sig_ports)
					self.sig_port_idx[dst_id] = (self.sig_port_idx[dst_id] + 1) % len(
						self.sig_ports)

					fp.write(
						"-a {} -Sdp {} -sp {} -rp {} -t 1000\n".format(dst_ip,
						                                               sig_port,
						                                               src_port,
						                                               dst_port))
					fp.flush()
				fp.close()
			commands = ["ITGSend", "/tmp/{}.itg.scripts".format(self.id)]

			thread = Thread(target=subprocess.run, args=(commands,))
			thread.start()
			sleep(60)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--id", required=True, help="host id")
	parser.add_argument("--n_ids",required=True,help="number of host in network")
	parser.add_argument("--dst_ids_fn",required=True,help="dst ids file path")

	args = parser.parse_args()

	with open(args.dst_ids_fn, "r") as fp:
		dst_ids = list(map(int,fp.readlines()))
		fp.close()

	gen = DummyGen(10, int(args.id), dst_ids,n_ids=int(args.n_ids))
	gen.start()
