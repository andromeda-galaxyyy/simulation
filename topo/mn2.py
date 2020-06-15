from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call
import os
from py2_utils import check_file, load_json, load_pkl, save_pkl, save_json
import time
from mininet.node import Controller
from os import environ
from argparse import ArgumentParser

from mininet.node import Controller
from os import environ


def get_prj_root():
	return os.path.dirname(os.path.abspath(__file__))


topo_dir = os.path.join(get_prj_root(), "files")

generator_script = os.path.join(get_prj_root(), "../traffic/scapy_generator.py")


def generate_ip(id):
	id = int(id) + 1
	if 1 <= id <= 254:
		return "10.0.0." + str(id)
	if 255 <= id <= 255 * 254 + 253:
		return "10.0." + str(id // 254) + "." + str(id % 254)
	raise Exception("Cannot support id address given a too large id")


def generate_mac(id):
	id = int(id) + 1

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

	raw_str = base_16(id)
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


def read_topo(fn="topo.json"):
	'''
	read topo given json file
	bw b/s
	delay ms
	loss %
	:param fn: json file name
	:return: topo
	'''
	fn = os.path.join(topo_dir, fn)
	check_file(fn)
	topo = load_json(fn)["topo"]

	# check topo
	num_nodes = len(topo)
	assert num_nodes > 0
	assert len(topo[0]) == num_nodes
	for i in range(num_nodes):
		for j in range(i + 1, num_nodes):
			assert len(topo[i][j]) == 4
	return topo


class TopoManager:
	def __init__(self, fn="topo.json", n_hosts_per_switch=1):
		self.topo = read_topo(fn)
		self.hosts = []
		self.num_switches = 0
		self.switches = []
		self.host_macs = []
		self.host_ips = []
		self.n_hosts_per_switch = n_hosts_per_switch

	def __write_ip_file(self):
		for switch_id in range(self.num_switches):
			other_switches = list(filter(lambda x: x != switch_id, list(range(self.num_switches))))
			other_ips = []
			for i in range(self.n_hosts_per_switch):
				other_ips.extend(
					[generate_ip(self.n_hosts_per_switch * other_id + i) for other_id in
					 other_switches])

			for host_idx in range(self.n_hosts_per_switch):
				host_id = switch_id * self.n_hosts_per_switch + host_idx
				self_ip = generate_ip(host_id)
				with open(os.path.join(topo_dir, "{}.ips".format(self_ip)), "w") as fp:
					fp.write("{}\n".format(self_ip))
					for other_ip in other_ips:
						fp.write("{}\n".format(other_ip))
					fp.flush()
					fp.close()

	def __write_id_file(self):
		for switch_id in range(self.num_switches):
			other_switches = list(filter(lambda x: x != switch_id, list(range(self.num_switches))))
			other_ids = []
			for i in range(self.n_hosts_per_switch):
				other_ids.extend(
					[self.n_hosts_per_switch * other_id + i for other_id in other_switches])

			for host_idx in range(self.n_hosts_per_switch):
				host_id = switch_id * self.n_hosts_per_switch + host_idx
				with open(os.path.join(topo_dir, "{}.hostids".format(host_id)), "w") as fp:
					for other_ip in other_ids:
						fp.write("{}\n".format(other_ip))
					fp.flush()
					fp.close()

	def set_up_mininet(self, controller="default", socket_port=10000):

		if controller == "default":
			controller_ip = "127.0.0.1"
			net = Mininet(topo=None, controller=None, ipBase="10.0.0.0/8")
		else:
			controller_ip, controller_port = controller.split(":")
			controller_port = int(controller_port)
			net = Mininet(topo=None, controller=None, ipBase="10.0.0.0/8")
			c = RemoteController('c', controller_ip, controller_port)
			net.addController(c)

		topo = self.topo
		num_switches = len(topo)
		self.num_switches = num_switches
		info("Setting up {} switches".format(num_switches))
		# add nat

		ips = []

		for i in range(num_switches):
			s = net.addSwitch("s{}".format(i), cls=OVSKernelSwitch, protocols=["OpenFlow13"])
			self.switches.append(s)
			for host_idx in range(self.n_hosts_per_switch):
				host_id = i * self.n_hosts_per_switch + host_idx

				h = net.addHost("h{}".format(host_id),
				                cls=Host,
				                ip=generate_ip(host_id),
				                defaultRoute=None,
				                mac=generate_mac(host_id)
				                )
				self.hosts.append(h)
				net.addLink(s, h)

		self.host_ips = ips
		self.__write_id_file()
		# return

		for i in range(num_switches):
			src = "s{}".format(i)
			for j in range(i + 1, num_switches):
				dst = "s{}".format(j)
				if -1 in topo[i][j]: continue
				bw, delay, loss, sc = topo[i][j]
				# bw="{}m".format(bw)
				delay = "{}ms".format(delay)
				# loss=str(loss)
				# net.addLink(src,dst,cls=TCLink,bw=bw,delay=delay,loss=loss)
				net.addLink(src, dst)
		# set up nat
		net.addNAT(ip="10.0.255.254/8").configDefault()
		net.start()

		# set nat
		for host in self.hosts:
			host.cmd("route add default gw 10.0.255.254")

		for idx, host in enumerate(self.hosts):
			ip = generate_ip(idx)
			for sigport in [1030,1031,1032,1033,1034]:
				host.cmd("nohup {} {}>/tmp/receiver_{}_{}.log 2>&1 &".format(receiver_script,sigport,ip,sigport))
		# host.cmd(
		# 	"{} >/tmp/sender_{}.log 2>&1 &".format(daemon_sender_script, ip))

		time.sleep(3)
		for idx, host in enumerate(self.hosts):
			ids_fn = os.path.join(topo_dir, "{}.hostids".format(idx))
			host.cmd(
				"nohup python3 {} --id {} --n_ids {} --dst_ids_fn {} >/tmp/{}_python.log 2>&1 &".format(
					generator_script,
					idx,
					len(self.hosts),
					ids_fn,
					idx
					))

		CLI(net)
		for idx, host in enumerate(self.hosts):
			host.cmd("pkill -f %?sender.sh")
			host.cmd("pkill -f ITGSend")
			host.cmd("pkill -f %?receiver.sh")
			host.cmd("pkill -f ITGRecv")
			host.cmd("pkill -f %?manager.sh")
			host.cmd("pkill -f DummyManager")
			host.cmd("pkill -f python3")

		net.stop()


if __name__ == '__main__':
	builder = TopoManager()
	parser = ArgumentParser()
	parser.add_argument("--controller_ip", type=str, default="192.168.64.1",
	                    help="ryu ip,note that cannot "
	                         "be be localhost or "
	                         "127.0.0.1")
	parser.add_argument("--controller_port", type=int, default=6633)
	parser.add_argument("--controller_socket_port", type=int, default=1026)
	parser.add_argument("-n", type=int, default=1, help="number of hosts per switch")
	args = parser.parse_args()
	if args.controller_ip == "127.0.0.1" or args.controller_ip == "localhost":
		print("Ryu controller ip cannot be localhost or 127.0.0.1!")
		exit(-1)

	builder.set_up_mininet("{}:{}".format(args.controller_ip, args.controller_port), 1026)
