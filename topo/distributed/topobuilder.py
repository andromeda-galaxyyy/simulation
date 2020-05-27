import os
import subprocess
from typing import List, Set, Dict, Tuple, Optional
import hashlib
from loguru import logger
from path_utils import get_prj_root


# todo mtu size


def generate_ip(id):
	id = int(id) + 1
	if 1 <= id <= 254:
		return "10.0.0." + str(id)
	if 255 <= id <= 255 * 254 + 253:
		return "10.0." + str(id // 254) + "." + str(id % 254)
	raise Exception("Cannot support id address given a too large id")


def generate_nat_ip(id):
	id = int(id) + 1
	if 1 <= id <= 254:
		return "10.1.0." + str(id)
	if 255 <= id <= 255 * 254 + 253:
		return "10.1." + str(id // 254) + "." + str(id % 254)
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


def add_veth(p1, p2):
	os.system("ip link add {} type veth peer name {}".format(p1, p2))


def attach_interface_to_sw(s: str, port: str):
	os.system("ovs-vsctl add-port {} {}".format(s, port))


def detach_interface_from_sw(s: str, port: str):
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
	#add delay
	# bandwidth=1000*int(bandwidth)
	os.system("tc qdisc add dev {} root handle 1:0 netem delay {}ms".format(interface,delay))
	os.system("tc qdisc add dev {} parent 1:1 handle 10: tbf rate {}mbit buffer 10000000 limit 20000000".format(interface,bandwidth))
	# os.system(
	# 	"tc qdisc add dev {} root netem delay {}ms rate {}mbit".format(interface, delay,
	# 	                                                                 bandwidth))


def set_dpid(sw_id, dpid):
	sname = "s{}".format(sw_id)
	os.system("ovs-vsctl set bridge {} other-config:datapath-id={}".format(sname, dpid))


def run_command_in_namespace(namespace, commands):
	os.system("ip netns exec {} {}".format(namespace, commands))


def del_ns(namespace):
	os.system("ip netns del {}".format(namespace))


def set_mtu(intf: str, mtu: int):
	mtu = int(mtu)
	os.system("ifconfig {} mtu {}".format(intf, mtu))


def set_ns_mtu(ns: str, intf: str, mtu: int):
	mtu = int(mtu)
	os.system("ip netns exec {} ifconfig {} mtu {}".format(ns, intf, mtu))


def set_mac_addr(intf: str, mac):
	os.system("ip link set {} address {}".format(intf, mac))


def set_ns_mac_addr(ns: str, intf: str, mac: str):
	os.system("ip netns exec {} ip link set {} address {}".format(ns, intf, mac))


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
	add_tc(saport, delay, rate, loss)
	add_tc(sbport, delay, rate, loss)
	# os.system("tc qdisc add dev {} root netem rate {} latency {}".format(saport, rate, delay))
	# os.system("tc qdisc add dev {} root netem rate {} latency {}".format(sbport, rate, delay))
	# todo loss

	return saport, sbport


def connect_non_local_switches(sa_id, local_ip, sb_id, remote_ip, grekey,  rate, delay, loss,gre_mtu=1554):
	local_sw = "s{}".format(sa_id)
	remote_sw = "s{}".format(sb_id)
	grename = "gre{}-{}".format(local_sw, remote_sw)
	# delete exists gre links
	# os.system("ip link del {}".format(grename))
	del_interface(grename)
	os.system("ip link add {} type gretap local {} remote {} ttl 64 key {}".format(
		grename,
		local_ip,
		remote_ip,
		grekey
	))
	os.system("ip link set dev {} up".format(grename))
	gre_mtu=int(gre_mtu)
	set_mtu(grename,gre_mtu)
	for x in ["gro", "tso", "gso"]:
	# for x in ["tso"]:
		os.system("ethtool -K {} {} off".format(grename, x))
	# pass
	# set_mtu(grename,1560)
	attach_interface_to_sw(local_sw, grename)
	add_tc(grename, delay, rate, loss)
	return grename


# todo mtu
def add_hosts_to_switches(switch_id, k,vhost_mtu=1500):
	ovsname = "s{}".format(switch_id)
	mtu=int(vhost_mtu)
	for idx in range(k):
		host_id = switch_id * k + idx
		hostname = "h{}".format(host_id)
		host_port = "{}-eth0".format(hostname)
		ovs_port = "{}-{}".format(ovsname, hostname)

		os.system("ip netns add {}".format(hostname))
		os.system("ip link add {} type veth peer name {}".format(host_port, ovs_port))
		os.system("ip link set {} netns {}".format(host_port, hostname))

		# up host interface
		# 10.0.0.1/16
		# 修改子网为10.0.0.1/16
		os.system(
			"ip netns exec {} ifconfig {} {}/16".format(hostname, host_port, generate_ip(host_id)))

		os.system("ip netns exec {} ifconfig lo up".format(hostname))
		set_ns_mac_addr(hostname, host_port, generate_mac(host_id))
		# todo mtu size
		set_ns_mtu(hostname, host_port, mtu)

		# attach ovs port
		attach_interface_to_sw(ovsname, ovs_port)
		up_interface(ovs_port)


def add_ovs(switch_id, controller: str):
	ovs_name = "s{}".format(switch_id)
	logger.debug("set up switch {}".format(ovs_name))
	os.system("ovs-vsctl add-br {}".format(ovs_name))
	os.system("ovs-vsctl set-controller {} tcp:{}".format(ovs_name, controller))
	logger.debug("set up switch {} done".format(ovs_name))


def del_ovs(ovs):
	if "s" not in ovs:
		ovs = "s{}".format(ovs)
	os.system("ovs-vsctl del-br {}".format(ovs))


def del_hosts(ovs, k):
	if "s" not in ovs:
		ovs = "s{}".format(ovs)

	for idx in range(k):
		host_id = ovs * k + idx
		host_port = "{}-eth0".format(host_id)
		hostname = "h{}".format(host_id)
		ovs_port = "{}-{}".format(hostname, ovs)
		os.system("ip netns del {}".format(hostname))
		os.system("ip link del {}".format(host_port))


def del_local_link(link_name):
	del_interface(link_name)
	del_tc(link_name)


def get_swid_from_link(link: str):
	'''
	split switch from link name
	:param link: like gres1-s2 or s1-s2
	:return:
	'''
	if "gre" in link:
		link = link[3:]
	sa_name, sb_name = link.split("-")
	# return link.split("s")[1], link.split("s")[2]
	return int(sa_name[1:]), int(sb_name[1:])


def run_ns_binary(ns: str, bin: str, params: str, log_fn: str = "/tmp/log.log"):
	os.system("ip netns exec nohup {} {} {} >{} 2>&1 &".format(ns,bin,params,log_fn))


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

		logger.debug(self.local_switch_ids)
		logger.debug(self.remote_switches)

		self.local_links: list[str] = []
		self.nat_links: List[str] = []

		self.hosts: List[tuple] = []
		self.remote_ips: List[str] = config["workers_ip"]
		self.ip: str = config["workers_ip"][self.id]
		self._set_up_switches()
		mtu=self.config["host_mtu"]
		set_mtu(self.inetintf,mtu)

	def _set_up_switches(self):
		k = self.config["host_per_switch"]
		k = int(k)
		controller = self.config["controller"]
		# set up local switch
		vhost_mtu=self.config["vhost_mtu"]
		for sw_id in self.config["workers"][int(self.id)]:
			add_ovs(sw_id, controller)
			# set dpid
			set_dpid(sw_id, gen_dpid(sw_id))
			add_hosts_to_switches(sw_id, k,vhost_mtu)
		self.set_up_nat()

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
			logger.debug("Tearing down {}".format(sw_name))
			for idx in range(k):
				hostid = sid * k + idx
				hostname = "h{}".format(hostid)
				host_port = "{}-eth0".format(hostname)
				del_ns(hostname)
				del_interface(host_port)

				ovs_port = "{}-{}".format(sw_name, hostname)
				detach_interface_from_sw(sw_name, ovs_port)
				del_interface(ovs_port)
			del_ovs(sw_name)
			logger.debug("tear down {} done".format(sw_name))

	def _tear_down_gres(self):
		for gre in self.gres:
			s, _ = get_swid_from_link(gre)
			s = "s{}".format(s)
			detach_interface_from_sw(s, gre)
			del_tc(gre)
			down_interface(gre)
			del_interface(gre)

	def _tear_down_local_links(self):
		logger.debug(self.local_links)
		for link in self.local_links:
			del_local_link(link)

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
		self.nat_links = []

	def _setup_local_links(self, new_topo: List[List[Tuple]]):
		logger.debug("Setting up local links")
		new_links = []

		local_switch_ids = [int(x) for x in self.local_switch_ids]
		for sa_id in local_switch_ids:
			for sb_id in local_switch_ids:
				# remove duplicates
				if sa_id == sb_id or sa_id > sb_id: continue

				link = "s{}-s{}".format(sa_id, sb_id)
				reverse_link = "s{}-s{}".format(sb_id, sa_id)

				if -1 not in new_topo[sa_id][sb_id]:
					logger.debug("set up link {}".format(link))
					rate, delay, loss, _ = new_topo[sa_id][sb_id]
					new_links.append(link)
					if link not in self.local_links:
						connect_local_switches(sa_id, sb_id, rate, delay, loss)

					else:
						# exists in previous local links,
						# change tc
						del_tc(link)
						del_tc(reverse_link)
						add_tc(link, delay, rate, loss)
						add_tc(reverse_link, delay, rate, loss)
				else:
					# link is None
					if link in self.local_links:
						del_interface(link)
						del_interface(reverse_link)
		self.local_links = new_links

	def _diff_gre_links(self, new_topo: List[List[Tuple]]):
		logger.debug("Setting up gre links")
		new_gres = []
		local_sw_ids = [int(x) for x in self.local_switch_ids]
		remote_sw_ids = [int(x) for x in self.remote_switches.keys()]

		for sa_id in local_sw_ids:
			for sb_id in remote_sw_ids:

				key = self._gre_key(sa_id, sb_id)
				gretap = "gres{}-s{}".format(sa_id, sb_id)
				local_ip = self.ip
				# mapping from worker id to remote ip
				remote_ip = self.remote_ips[int(self.remote_switches[sb_id])]

				# if new_topo[sa_idx][sb_idx][0] == "None":
				if -1 in new_topo[sa_id][sb_id]:
					if gretap in self.gres:
						# take down gre
						down_interface(gretap)
						detach_interface_from_sw("s{}".format(sa_id), gretap)
						del_interface(gretap)
						del_tc(gretap)

				else:
					logger.debug("setting up gre {}".format(gretap))
					rate, delay, loss, _ = new_topo[sa_id][sb_id]
					new_gres.append(gretap)
					if gretap in self.gres:
						# del tc
						del_tc(gretap)
						add_tc(gretap, delay, rate, loss)
					else:
						# set up gre
						gre_mtu=self.config["gre_mtu"]

						connect_non_local_switches(sa_id, local_ip, sb_id, remote_ip, key, rate,
						                           delay, loss,gre_mtu)

		self.gres = new_gres

	def diff_topo(self, new_topo: List[List[Tuple]]):
		self._setup_local_links(new_topo)
		self._diff_gre_links(new_topo)

	# todo add nat
	def set_up_nat(self):
		logger.debug("Setting up nat")
		intf = self.inetintf

		worker_id = self.id
		nat2_ip = "10.1.0.254"
		logger.debug("nat out ip {}/16".format(nat2_ip))
		os.system("ovs-vsctl add-br nat")
		# os.system("ip link add nat1 type veth peer name nat2")
		add_veth("nat1", "nat2")
		os.system("ifconfig nat2 {}/16 up".format(nat2_ip))
		attach_interface_to_sw("nat", "nat1")
		# os.system("ovs-vsctl add-port nat nat1")
		os.system("ifconfig nat1 up")

		# set iptables
		os.system("iptables -A FORWARD -o {} -i {} -j ACCEPT".format("nat2", intf))
		os.system("iptables -A FORWARD -o {} -i {} -j ACCEPT".format(intf, "nat2"))
		os.system("iptables -t nat -A POSTROUTING -s 10.1.0.0/16 -o {} -j MASQUERADE".format(intf))

		# set add link to host
		# todo remove id from config file,
		# 改成从命令行接受
		k = int(self.config["host_per_switch"])
		local_switches = self.config["workers"][worker_id]

		for swid in local_switches:
			for hostidx in range(k):
				hostid = swid * k + hostidx
				hostname = "h{}".format(hostid)
				hnat = "{}-{}".format(hostname, "nat")
				nath = "{}-{}".format("nat", hostname)
				add_veth(hnat, nath)
				self.nat_links.append(hnat)
				self.nat_links.append(nath)
				# set netns
				os.system("ip link set {} netns {}".format(hnat, hostname))
				nat_ip = generate_nat_ip(hostid)
				os.system("ip netns exec {} ifconfig {} {}/16 up".format(hostname, hnat, nat_ip))
				# attach port
				os.system("ovs-vsctl add-port {} {}".format("nat", nath))
				os.system("ifconfig {} up".format(nath))

				# set default route
				os.system(
					"ip netns exec {} ip route add default via {}".format(hostname, nat2_ip))
		logger.debug("Setting up nat done")

	def _tear_down_nat(self):
		logger.debug("Tearing down nat")
		os.system("ovs-vsctl del-br nat")
		del_interface("nat1")
		del_interface("nat2")

		# tear down
		for p in self.nat_links:
			del_interface(p)
		# restore iptable rule to very basic
		# commands = """iptables-save | awk '/^[*]/ { print $1 }
        #              /^:[A-Z]+ [^-]/ { print $1 " ACCEPT" ; }
        #              /COMMIT/ { print $0; }' | iptables-restore"""
		commands="iptables -F"
		os.system(commands)
		logger.debug("Tearing down nat done")
