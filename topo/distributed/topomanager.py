import os
import subprocess
from typing import List, Set, Dict, Tuple, Optional
import hashlib
from path_utils import get_prj_root
from utils.common_utils import debug,info,err


def attach_interface(s: str, port: str):
	os.system("ovs-vsctl add-port {} {}".format(s, port))


def detach_interface(s: str, port: str):
	os.system("ovs-vsctl del-port {} {}".format(s, port))


def del_interface(port: str):
	os.system("ip link del dev {}".format(port))


def down_interface(port: str):
	subprocess.run(["ifconfig", port, "down"])


def up_interface(port: str):
	subprocess.run(["ifconfig", port, "up"])


def del_tc(interface: str):
	os.system("tc qdisc del dev {} root netem".format(interface))


def add_tc(interface: str, delay, bandwidth, loss):
	os.system(
		"tc qdisc add dev {} root netem latency {} rate {}".format(interface, delay, bandwidth))


def connect_local_switches(sa_id, sb_id, rate, delay, loss):
	sa_name = "s{}".format(sa_id)
	sb_name = "s{}".format(sb_id)
	saport = "{}-{}".format(sa_name, sb_name)
	sbport = "{}-{}".format(sb_name, sa_name)

	os.system("ip link add {} type veth peer name {}".format(saport, sbport))
	os.system("ifconfig {} up".format(saport))
	os.system("ifconfig {} up".format(sbport))
	os.system("ovs-vsctl add-port {} {}".format(sa_name, saport))
	os.system("ovs-vsctl add-port {} {}".format(sb_name, sbport))
	os.system("tc qdisc add dev {} root netem rate {} latency {}".format(saport, rate, delay))
	os.system("tc qdisc add dev {} root netem rate {} latency {}".format(sbport, rate, delay))
	# todo loss

	return saport, sbport


def connect_non_local_switches(sa_id, local_ip, sb_id, remote_ip, grekey, rate, delay, loss):
	local_sw = "s{}".format(sa_id)
	remote_sw = "s{}".format(sb_id)
	grename = "gre{}-{}".format(local_sw, remote_sw)
	# delete exists gre links
	os.system("ip link del {}".format(grename))
	os.system("ip link add {} type gretap local {} remote {} ttl 64 key {}".format(
		grename,
		local_ip,
		remote_ip,
		grekey
	))
	os.system("ip link set dev {} up".format(grename))
	for x in ["gro", "tso", "gso"]:
		os.system("ethtool -K {} {} off".format(grename, x))
	add_tc(grename, delay, rate, loss)
	return grename


# todo mtu
def add_hosts_to_switches(switch_id, k,vhost_mtu):
	ovsname = "s{}".format(switch_id)
	for idx in range(k):
		host_id = switch_id * k + idx
		hostname = "h{}".format(host_id)
		host_port = "{}-eth0".format(hostname)
		ovs_port = "{}-{}".format(hostname, ovsname)

		os.system("ip netns add {}".format(hostname))
		os.system("ip link add {} type veth peer name {}".format(host_port, ovs_port))
		os.system("ip link set {} netns {}".format(host_port, hostname))

		# up host interface
		os.system(
			"ip netns exec {} ifconfig {} {}/8".format(hostname, host_port, generate_ip(host_id)))
		os.system("ip netns exec {} ifconfig lo up".format(hostname))
		os.system("ip netns exec {} ifconfig {} mtu {}".format(hostname,host_port,vhost_mtu))

		# attach ovs port
		attach_interface(ovsname, ovs_port)
		up_interface(ovs_port)


def add_ovs(switch_id, controller: str):
	ovs_name = "s{}".format(switch_id)
	debug("set up switch {}".format(ovs_name))
	os.system("ovs-vsctl add-br {}".format(ovs_name))
	os.system("ovs-vsctl set-controller {} tcp: {}".format(ovs_name, controller))
	debug("set up switch {} done".format(ovs_name))


def del_ovs(switch_id):
	ovs_name = "s{}".format(switch_id)
	os.system("ovs-vsctl del br {}".format(ovs_name))


def del_hosts(switch_id, k):
	ovs = "s{}".format(switch_id)
	for idx in range(k):
		host_id = switch_id * k + idx
		host_port = "{}-eth0".format(host_id)
		hostname = "h{}".format(host_id)
		ovs_port = "{}-{}".format(hostname, ovs)
		os.system("ip netns del {}".format(hostname))
		os.system("ip link del {}".format(host_port))


def del_local_link(link_name):
	os.system("ip link del {}".format(link_name))
	del_tc(link_name)


def get_swid_from_link(link: str):
	if "gre" in link:
		link = link[3:]
	sa_name, sb_name = link.split("-")
	# return link.split("s")[1], link.split("s")[2]
	return int(sa_name[1:]), int(sb_name[1:])


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


class TopoManager:

	def __init__(self, config: dict, id_, inetintf: str):
		self.config: dict = config
		self.id = id_
		self.gres: List[str] = []
		self.inetintf = inetintf

		self.local_switch_ids: List[int] = config["workers"][self.id]

		# dict switch->worker id
		self.remote_switches = {}
		# parse remote switches
		for idx, switches in enumerate(config["workers"]):
			if self.id == int(idx): continue
			#
			for s in switches:
				self.remote_switches[s] = idx

		debug(self.local_switch_ids)
		debug(self.remote_switches)

		self.local_links: list[str] = []

		self.hosts: List[tuple] = []
		self.remote_ips: List[str] = config["workers_ip"]
		self.ip: str = config["workers_ip"][self.id]
		self._set_up_switches()

	def _set_up_switches(self):
		k = self.config["host_per_switch"]
		k = int(k)
		controller = self.config["controller"]
		# set up local switch
		vhost_mtu =self.config["vhost_mtu"]
		for sw_id in self.config["workers"][int(self.id)]:
			add_ovs(sw_id, controller)
			add_hosts_to_switches(sw_id, k,vhost_mtu)

	@staticmethod
	def _gre_key(sa_id, sb_id):
		'''
		return gre tunnel key,given two switch ids
		:param sa_id: id of switch a
		:param sb_id:  id of switch b
		:return:
		'''
		sa_id = int(sa_id)
		sb_id = int(sb_id)
		if sa_id > sb_id:
			return TopoManager._gre_key(sb_id, sa_id)
		# todo possable hash collisions
		m = hashlib.sha256()
		m.update(str.encode("s{}s{}".format(sa_id, sb_id)))
		return int(m.hexdigest(), 16) % 973

	def _tear_down_switch(self):
		k = self.config["host_per_switch"]
		k = int(k)
		for sid in self.local_switch_ids:
			sw_name = "s{}".format(sid)
			debug("Tearing down {}".format(sw_name))
			for idx in range(k):
				hostid = sid * k + idx
				hostname = "h{}".format(hostid)
				host_port = "{}-eth0".format(hostname)
				os.system("ip netns del {}".format(hostname))
				os.system("ip link del {}".format(host_port))
				ovs_port = "{}-{}".format(sw_name, hostname)
				os.system("ovs-vsctl del-port {} {}".format(sw_name, ovs_port))
				os.system("ovs-vsctl del-br {}".format(sw_name))
				os.system("ip link del {}".format(host_port))
			debug("tear down {} done".format(sw_name))

	def _tear_down_gres(self):
		for gre in self.gres:
			s, _ = get_swid_from_link(gre)
			s = "s{}".format(s)
			detach_interface(s, gre)
			del_tc(gre)
			down_interface(gre)
			del_interface(gre)

	def _tear_down_local_links(self):
		for link in self.local_links:
			del_local_link(link)

	def _tear_down_nat(self):
		worker_id = int(self.config["id"])
		nat_address = "10.{}.0.1".format(worker_id + 1)
		local_switches = self.config["workers"][worker_id]
		switch_id = local_switches[0]
		nat_port = "nat{}-s{}".format(worker_id, switch_id)
		os.system("ip link del {}".format(nat_port))

	def tear_down(self):
		# todo log
		self._tear_down_gres()
		self._tear_down_local_links()
		self._tear_down_switch()
		self._tear_down_nat()

		self.gres = []
		self.local_switch_ids = []
		self.remote_switches = {}
		self.local_links = []
		self.hosts = []

	def _diff_local_links(self, new_topo: List[List[Tuple]]):
		new_links = []

		local_switch_ids = [int(x) for x in self.local_switch_ids]
		for sa_id in local_switch_ids:
			for sb_id in local_switch_ids:
				# remove duplicates
				if sa_id == sb_id or sa_id > sb_id: continue

				if -1 not in new_topo[int(sa_id)][int(sb_id)]:
					rate, delay, loss, _ = new_topo[sa_id][sb_id]
					link = "s{}-s{}".format(sa_id, sb_id)
					reverse_link = "s{}-s{}".format(sb_id, sa_id)
					new_links.append(link)
					if link not in self.local_links:
						connect_local_switches(sa_id, sb_id, rate, delay, loss)

					else:
						# change tc
						del_tc(link)
						del_tc(reverse_link)
						add_tc(link, delay, rate, loss)
						add_tc(reverse_link, delay, rate, loss)
				else:
					# link is None
					link = "s{}-s{}".format(sa_id, sb_id)
					reverse_link = "s{}-s{}".format(sb_id, sa_id)
					if link in self.local_links:
						del_interface(link)
						del_interface(reverse_link)
		self.local_links = new_links

	def _diff_gre_links(self, new_topo: List[List[Tuple]]):
		new_gres = []
		local_sw_ids = [int(x) for x in self.local_switch_ids]
		remote_sw_ids = [int(x) for x in self.remote_switches.keys()]

		for sa_id in local_sw_ids:
			for sb_id in remote_sw_ids:

				key = self._gre_key(sa_id, sb_id)
				gretap = "gres{}-s{}".format(sa_id, sb_id)
				local_ip = self.ip
				remote_ip = self.remote_ips[int(self.remote_switches[sb_id])]

				# if new_topo[sa_idx][sb_idx][0] == "None":
				if -1 in new_topo[sa_id][sb_id]:
					if gretap in self.gres:
						# take down gre
						down_interface(gretap)
						detach_interface("s{}".format(sa_id), gretap)
						del_interface(gretap)

				else:
					rate, delay, loss, _ = new_topo[sa_id][sb_id]
					new_gres.append(gretap)
					if gretap in self.gres:
						# del tc
						del_tc(gretap)
						add_tc(gretap, delay, rate, loss)
					else:
						# set up gre
						connect_non_local_switches(sa_id, local_ip, sb_id, remote_ip, key, rate,
						                           delay, loss)

		self.gres = new_gres

	def set_up_nat(self, nat_addr):
		# find a switch
		worker_id = int(self.config["id"])
		local_switches = self.config["workers"][worker_id]
		switch_id = local_switches[0]
		nat_port = "nat{}-s{}".format(worker_id, switch_id)
		switch_port = "s{}-nat{}".format(switch_id, worker_id)

		os.system("ip link add {} type veth peer name {}".format(nat_port, switch_port))
		os.system("ifconfig {} {}/8 up".format(nat_port, nat_addr))
		os.system("ifconfig {} up".format(switch_port))

		attach_interface("s{}".format(switch_id), switch_port)
		os.system("iptables -A FORWARD -o {} -i {} -j ACCEPT".format(self.inetintf, nat_port))
		os.system("iptables -A FORWARD -i {} -o {} -j ACCEPT".format(self.inetintf, nat_port))
		os.system("iptables -t nat -A POSTROUTING -s {}/8 -o {} -j MASQUERADE".format(nat_addr,
		                                                                              self.inetintf))
		os.system('sysctl net.ipv4.ip_forward=1')

		k = self.config["host_per_switch"]
		k = int(k)
		# set up host
		for swid in local_switches:
			for hostidx in range(k):
				hostid = swid * k + hostidx
				hostname = "h{}".format(hostid)
				os.system("ip netns exec {} route add default gw {}".format(hostname, nat_addr))
		debug("NAT set done")

	def diff_topo(self, new_topo: List[List[Tuple]]):
		self._diff_local_links(new_topo)
		self._diff_gre_links(new_topo)
		# todo add nat
		workder_id = int(self.config["id"])
		nat_address = "10.{}.0.1".format(workder_id + 1)
