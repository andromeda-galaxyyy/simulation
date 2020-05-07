import socket

import dpkt


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


def get_pkt_key(sip, sport, dip, dport, proto):
	return "{}-{}-{}-{}-{}-{}".format(sip, sport, dip, dport, proto)


class packet:
	def __init__(self, sip, sport, dip, dport, proto, size, timestamp):
		self.sip = sip
		self.sport = sport
		self.dip = dip
		self.dport = dport
		self.proto = proto
		self.size = size
		self.timestamp = timestamp

	def get_key(self):
		return "{}-{}-{}-{}-{}".format(self.sip, self.sport, self.dip, self.dport, self.proto)


def compare(a: packet, b: packet) -> int:
	'''

	:param a: packet a
	:param b: packet b
	:return: 0 for nothing same
			1 for totally same
			-1 for reverse same
	'''
	return 1


class Parser(object):
	def __init__(self):
		self.file = "/Volumes/DATA/dataset/converted_iot/16-09-23.pcap"
		self.tcp_flows = {}
		self.udp_flows = {}

	def readPcap(self):
		try:
			fp = open(self.file, 'rb')
		except Exception as e:
			print("Error opening file {}".format(self.file))
			raise e

		pcap = dpkt.pcap.Reader(fp)
		start = 0;
		count = 1
		for ts, buf in pcap:
			start = ts
			break

		for ts, buf in pcap:
			timestamp = ts - start
			try:
				eth = dpkt.ethernet.Ethernet(buf)
			except Exception as e:
				continue
			if eth.type != dpkt.ethernet.ETH_TYPE_IP:
				continue
			ip = eth.data
			if ip.p == dpkt.ip.IP_PROTO_TCP:
				tcp = ip.data
				pkt = packet(inet_to_str(ip.src), tcp.sport, inet_to_str(ip.dst), tcp.dport, 'tcp',
							 len(buf), timestamp)
				key = pkt.get_key()
				if key not in self.tcp_flows.keys():
					self.tcp_flows[key] = [pkt]
				else:
					self.tcp_flows[key].append(pkt)
			elif ip.p == dpkt.ip.IP_PROTO_UDP:
				udp = ip.data
				pkt = packet(inet_to_str(ip.src), udp.sport, inet_to_str(ip.dst), udp.dport, 'udp',
							 len(buf),
							 timestamp)
				key = pkt.get_key()
				if key not in self.udp_flows.keys():
					self.udp_flows[key] = [pkt]
				else:
					self.udp_flows[key].append(pkt)
			else:
				continue
	# TODO log packet counts

p=Parser()
p.readPcap()
