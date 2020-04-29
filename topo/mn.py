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
from py2_utils import check_file,load_json,load_pkl,save_pkl,save_json

def get_prj_root():
	return os.path.dirname(os.path.abspath(__file__))

topo_dir = os.path.join(get_prj_root(), "files")


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
		self.hosts=[]
		self.switches=[]
		self.host_macs=[]
		self.host_ips=[]

	def set_up_mininet(self, controller="default"):
		net = Mininet(topo=None, controller=None, ipBase="10.0.0.0/8")
		c=RemoteController('c',controller,6633) if controller!="default" else None
		net.addController(c)
		topo = self.topo
		nodes = len(topo)
		info("Setting up {} switches".format(nodes))

		macs = []
		ips = []
		mac_prefix = "00:00:00:00:00:"
		ip_prefix="10.0.0."

		for i in range(nodes):
			s = net.addSwitch("s{}".format(i), cls=OVSKernelSwitch, protocols=["OpenFlow13"])
			self.switches.append(s)
			mac_suffix = str((i + 1) / 16) + str((i + 1) % 16)
			ip_suffix=str(i+1)
			macs.append(mac_prefix+mac_suffix)
			ips.append(ip_prefix+ip_suffix)

			h=net.addHost("h{}".format(i),
			              cls=Host,
			              ip=(ip_prefix+ip_suffix),
			              defaultRoute=None,
			              mac=(mac_prefix+mac_suffix)
			              )
			self.hosts.append(h)
			net.addLink(s,h)
		#add link between switches

		for i in range(nodes):
			src="s{}".format(i)
			for j in range(i+1,nodes):
				dst="s{}".format(j)
				bw,delay,loss=topo[i][j]
				if bw is None or bw=="None":continue
				# bw="{}m".format(bw)
				delay="{}ms".format(delay)
				# loss=str(loss)
				net.addLink(src,dst,cls=TCLink,bw=bw,delay=delay,loss=loss)
		net.start()
		CLI(net)
		net.stop()


if __name__ == '__main__':
    manager=TopoManager()
    manager.set_up_mininet("127.0.0.1")









