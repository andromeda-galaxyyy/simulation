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



def get_prj_root():
	return os.path.dirname(os.path.abspath(__file__))


topo_dir = os.path.join(get_prj_root(), "files")

daemon_sender_script = os.path.join(get_prj_root(), "../traffic/sender.sh")
receiver_script = os.path.join(get_prj_root(), "../traffic/receiver.sh")
manager_script = os.path.join(get_prj_root(), "../traffic/manager.sh")


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
			assert len(topo[i][j]) == 3
	return topo


class TopoManager:
	def __init__(self, fn="topo.json"):
		self.topo = read_topo(fn)
		self.hosts = []
		self.switches = []
		self.host_macs = []
		self.host_ips = []

	def __write_ip_file(self):
		for ip in self.host_ips:
			with open(os.path.join(topo_dir, "{}.ips".format(ip)), "w") as fp:
				fp.write("{}\n".format(ip))
				other_ips = list(filter(lambda x: x != ip, self.host_ips))
				for other_ip in other_ips:
					fp.write("{}\n".format(other_ip))
				fp.flush()
				fp.close()

	def set_up_mininet(self, controller="default"):
		net = Mininet(topo=None, controller=None, ipBase="10.0.0.0/8")
		c = RemoteController('c', '0.0.0.0', 6633)
		net.addController(c)
		topo = self.topo
		nodes = len(topo)
		info("Setting up {} switches".format(nodes))
		# add nat

		macs = []
		ips = []
		mac_prefix = "00:00:00:00:00:"
		ip_prefix = "10.0.0."

		for i in range(nodes):
			s = net.addSwitch("s{}".format(i), cls=OVSKernelSwitch, protocols=["OpenFlow13"])
			self.switches.append(s)
			mac_suffix = str((i + 1) / 16) + str((i + 1) % 16)
			ip_suffix = str(i + 1)
			macs.append(mac_prefix + mac_suffix)
			ips.append(ip_prefix + ip_suffix)

			h = net.addHost("h{}".format(i),
			                cls=Host,
			                ip=(ip_prefix + ip_suffix),
			                defaultRoute=None,
			                mac=(mac_prefix + mac_suffix)
			                )
			self.hosts.append(h)
			net.addLink(s, h)
		self.host_ips = ips
		self.__write_ip_file()

		for i in range(nodes):
			src = "s{}".format(i)
			for j in range(i + 1, nodes):
				dst = "s{}".format(j)
				bw, delay, loss = topo[i][j]
				if bw is None or bw == "None": continue
				# bw="{}m".format(bw)
				delay = "{}ms".format(delay)
				# loss=str(loss)
				# net.addLink(src,dst,cls=TCLink,bw=bw,delay=delay,loss=loss)
				net.addLink(src, dst)

		net.addNAT(ip="10.0.0.254/8").configDefault()
		net.start()

		# set nat
		for host in self.hosts:
			host.cmd("route add default gw 10.0.0.254")

		for idx, host in enumerate(self.hosts):
			host.cmd("{} >/tmp/receiver_{}.log 2>&1 &".format(receiver_script, self.host_ips[idx]))
			host.cmd(
				"{} >/tmp/sender_{}.log 2>&1 &".format(daemon_sender_script, self.host_ips[idx]))

		time.sleep(3)
		for idx, host in enumerate(self.hosts):
			ip_file = os.path.join(topo_dir, "{}.ips".format(self.host_ips[idx]))
			host.cmd("{} {} >/tmp/manager_{}.log 2>&1 &".format(manager_script, ip_file,
			                                                   self.host_ips[idx]))

		CLI(net)
		for idx, host in enumerate(self.hosts):
			host.cmd("pkill -f %?sender.sh")
			host.cmd("pkill -f ITGSend")
			host.cmd("pkill -f %?receiver.sh")
			host.cmd("pkill -f ITGRecv")
			host.cmd("pkill -f %?manager.sh")
			host.cmd("pkill -f ITGManager")

		net.stop()


if __name__ == '__main__':
	manager = TopoManager()
	manager.set_up_mininet("127.0.0.1")
