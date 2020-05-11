import os
import subprocess
from typing import List, Set, Dict, Tuple, Optional
import hashlib
from loguru import logger
no_output=">/dev/null"

#TODO move scripts directory inside current directory

def attach_interface(s: str, port: str):
	os.system("ovs-vsctl add-port {} {}".format(s,port))


def detach_interface(s: str, port: str):
	os.system("ovs-vsctl del-port {} {}".format(s,port))


def del_interface(port: str):
	os.system("ip link del dev {}".format(port))


def down_interface(port: str):
	subprocess.run(["ifconfig",port,"down"])


def up_interface(port: str):
	subprocess.run(["ifconfig",port,"up"])


def del_tc(interface: str):
	os.system("tc qdisc del dev {} root netem".format(interface))


def add_tc(interface: str, delay, bandwidth):
	os.system("tc qdisc add dev {} root netem latency {} rate {}".format(interface, delay,bandwidth))


def split_switches_from_link(link: str):
	if "gre" in link:
		link = link[3:]
	return link.split("s")[1], link.split("s")[2]

def generate_host_ip(self,sw_id):
	sw_id=int(sw_id)
	assert sw_id<253*253
	a=sw_id/253+1
	b=sw_id%253+1
	return "10.0.{}.{}".format(a,b)

# todo put tc command in a seperate script
class TopoManager:

	def __init__(self, config: dict):
		self.config: dict = config
		self.id = int(config["id"])
		self.gres: List[str] = []

		self.switches: List[int] = config["workers"][self.id]

		#dict switch->worker id
		self.remote_switches: dict[str][int] = {}
		# parse remote switches
		for idx, switches in enumerate(config["workers"]):
			if self.id == int(idx): continue
			#
			for s in switches:
				self.remote_switches[s] = idx

		logger.debug(self.switches)
		logger.debug(self.remote_switches)

		self.local_links: list[str] = []

		self.hosts: List[tuple] = []
		self.remote_ips: List[str] = config["workers_ip"]
		self.ip: str = config["workers_ip"][self.id]
		self._set_up_switches()
	



	def _set_up_switches(self):
		scripts_dir = self.config["scripts_dir"]
		controller = self.config["controller"]
		script = "create_switch.sh"
		script_path = os.path.join(scripts_dir, script)
		worker_id = int(self.id)
		for sw_id in self.config["workers"][worker_id]:
			host = "h{}".format(sw_id)
			host_ip=self._generate_host_ip(sw_id)
			logger.debug("host ip for {} is {}".format(sw_id,host_ip))
			# todo mac address
			subprocess.run(
				[script_path,"s{}".format(sw_id), host, host_ip, controller])

	def _gre_key(self, sa_id, sb_id):
		'''
		return gre tunnel key,given two switch ids
		:param sa_id: id of switch a
		:param sb_id:  id of switch b
		:return:
		'''
		sa_id = int(sa_id)
		sb_id = int(sb_id)
		if sa_id > sb_id:
			return self._gre_key(sb_id, sa_id)
		# todo possable hash collisions
		m=hashlib.sha256()
		m.update(str.encode("s{}s{}".format(sa_id,sb_id)))
		return int(m.hexdigest(),16)%973

	def _script_path(self, script):
		scripts_dir = self.config["scripts_dir"]
		return os.path.join(scripts_dir, script)

	def _tear_down_switch(self):
		script = self._script_path("down_switch.sh")
		for sid in self.switches:
			subprocess.run(["sudo", script, "s{}".format(sid),"h{}".format(sid)])

	def _tear_down_gres(self):
		for gre in self.gres:
			s, _ = split_switches_from_link(gre)
			detach_interface(s, gre)
			del_tc(gre)
			down_interface(gre)
			del_interface(gre)

	def _tear_down_local_links(self):
		script = self._script_path("delete_port.sh")
		for link in self.local_links:
			subprocess.run([script, link])

	def tear_down(self):
		# todo log
		self._tear_down_gres()
		self._tear_down_local_links()
		self._tear_down_switch()
		self.gres = []
		self.switches = []
		self.remote_switches = {}
		self.local_links = []
		self.hosts = []

	def _diff_local_links(self, new_topo: List[List[Tuple]]):
		new_links = []

		switch_idxes = [int(x)-1 for x in self.switches]
		logger.debug(switch_idxes)
		logger.debug(new_topo)
		for sa_idx in switch_idxes:
			for sb_idx in switch_idxes:
				# remove duplicates
				if sa_idx == sb_idx or sa_idx > sb_idx: continue

				if new_topo[sa_idx][sb_idx][0] != "None":
					delay, rate = new_topo[sa_idx][sb_idx]
					link = "s{}s{}".format(sa_idx+1, sb_idx+1)
					reverse_link = "s{}s{}".format(sb_idx+1, sa_idx+1)
					new_links.append(link)
					script = self._script_path("local_link.sh")
					if link not in self.local_links:
						os.system("{} s{} s{} {} {}".format(script,sa_idx+1,sb_idx+1,delay,rate))
					else:
						# change tc
						del_tc(link)
						del_tc(reverse_link)
						add_tc(link, delay, rate)
						add_tc(reverse_link, delay, rate)
				else:
					# link is None
					link = "s{}s{}".format(sa_idx+1, sb_idx+1)
					reverse_link = "s{}s{}".format(sb_idx+1, sa_idx+1)
					if link in self.local_links:
						del_interface(link)
						del_interface(reverse_link)
		self.local_links = new_links

	def _diff_gre_links(self, new_topo: List[List[Tuple]]):
		script = self._script_path("gretap.sh")
		new_gres = []
		switch_idxes=[int(x)-1 for x in self.switches]
		remote_switch_idxes=[int(x) -1 for x in self.remote_switches.keys()]

		for sa_idx in switch_idxes:
			for sb_idx in remote_switch_idxes:

				#delay, rate = self.remote_[int(sa_idx)][int(sb_idx)]
				key = self._gre_key(sa_idx+1, sb_idx+1)
				gretap = "gres{}s{}".format(sa_idx+1, sb_idx+1)
				local_ip = self.ip
				logger.debug(self.remote_ips)
				logger.debug(self.remote_switches)
				logger.debug(sb_idx)
				remote_ip = self.remote_ips[int(self.remote_switches[sb_idx+1])]

				if new_topo[sa_idx][sb_idx][0]=="None":
					if gretap in self.gres:
						# take down gre
						down_interface(gretap)
						detach_interface("s{}".format(sa_idx), gretap)
						del_interface(gretap)
				elif new_topo[sa_idx][sb_idx][0]!="None":
					delay, rate = new_topo[int(sa_idx)][int(sb_idx)]
					new_gres.append(gretap)
					if gretap in self.gres:
						# del tc
						del_tc(gretap)
						add_tc(gretap, delay, rate)
					else:

						os.system("{} {} {} {} {} {} {}".format(script,gretap,local_ip,remote_ip,key,delay,rate))
						# os.system("ifconfig {} up".format(gretap))
						attach_interface("s{}".format(sa_idx+1),gretap)

		self.gres = new_gres

	def diff_topo(self, new_topo: List[List[Tuple]]):
		self._diff_local_links(new_topo)

		self._diff_gre_links(new_topo)


