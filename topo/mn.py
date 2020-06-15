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

generator = os.path.join(get_prj_root(), "../traffic/gogen/gen/gen")
script = os.path.join(get_prj_root(), "../traffic/never.stop.sh")
listener = os.path.join(get_prj_root(), "../traffic/gogen/golisten/golisten")


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


def gen_dpid(sid):
	sid = int(sid) + 1

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

	raw_str = base_16(sid)
	zero_padding_len = 16 - len(raw_str)
	if zero_padding_len < 0:
		raise Exception("Two large switch id")
	return ("0" * zero_padding_len) + raw_str


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
			print("Controller ip {} Controller port {}".format(controller_ip, controller_port))
			net = Mininet(topo=None, controller=None, ipBase="10.0.0.0/8")
			c = RemoteController('c', controller_ip, controller_port)
			net.addController(c)

		topo = self.topo
		num_switches = len(topo)
		self.num_switches = num_switches
		print("Setting up {} switches".format(num_switches))
		# add nat

		ips = []

		for i in range(num_switches):
			s = net.addSwitch("s{}".format(i), cls=OVSKernelSwitch, protocols=["OpenFlow13"],
			                  dpid=gen_dpid(i))
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
			for j in range(i, num_switches):
				dst = "s{}".format(j)
				if -1 in topo[i][j]: continue
				bw, delay, loss, sc = topo[i][j]
				delay = "{}ms".format(delay)
				net.addLink(src, dst)
		# set up nat
		net.addNAT(ip="10.0.255.254/8").configDefault()
		net.build()
		net.start()
		#
		# # set nat
		for host in self.hosts:
			# pass
			host.cmd("route add default gw 10.0.255.254")
		for idx, host in enumerate(self.hosts):
			continue
			commands = "nohup {} --intf h{}-eth0 --src 10.0.0.0/8 --dst 10.0.0.0/8 >/tmp/{}.listener.log 2>&1 &".format(
				listener, idx, idx)
			host.cmd(commands)
		# time.sleep(3)

		for idx, host in enumerate(self.hosts):
			# if idx!=0:continue
			# continue
			# if idx % 4 != 0: continue
			# dstIdFn="/home/stack/code/graduate/sim/system/topo/files/{}.hostids".format(idx)
			dstIdFn = os.path.join(topo_dir, "{}.hostids".format(idx))
			# pkt_dir="/home/stack/code/graduate/sim/system/traffic/gogen/pkts"
			pkt_dir = os.path.join(get_prj_root(), "../traffic/gogen/pkts")
			# pkt_dir="/tmp/video"
			comands = "nohup {} {} --id {} --dst_id {} --pkts {} --mtu 1500 -emppkt 64 --int h{}-eth0 " \
			          "--ws {} --cip {} --debug=false --cport {} >/tmp/{}.gen.log 2>&1 &".format(
				script,
				generator,
				idx,
				dstIdFn,
				pkt_dir,
				idx,
				10,
				controller_ip,
				socket_port,
				idx
			)
			host.cmd(comands)

		CLI(net)
		for idx, host in enumerate(self.hosts):
			host.cmd("pkill -f gen")
			host.cmd("pkill -f golisten")

		net.stop()


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("--controller_ip", type=str, default="192.168.1.90",
	                    help="ryu ip,note that cannot "
	                         "be be localhost or "
	                         "127.0.0.1")
	parser.add_argument("--controller_port", type=int, default=6633)
	parser.add_argument("--controller_socket_port", type=int, default=1026)
	parser.add_argument("--n", type=int, default=1, help="number of hosts per switch")
	parser.add_argument("--topo", type=str, default="topo.json", help="Path to topo json")
	args = parser.parse_args()
	if args.controller_ip == "127.0.0.1" or args.controller_ip == "localhost":
		print("Ryu controller ip cannot be localhost or 127.0.0.1!")
		exit(-1)

	builder = TopoManager(fn=args.topo, n_hosts_per_switch=int(args.n))

	builder.set_up_mininet("{}:{}".format(args.controller_ip, args.controller_port), 1026)
