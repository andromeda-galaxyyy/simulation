from scapy.layers.inet import IP, UDP, TCP
from scapy.layers.l2 import Ether
from scapy.all import *





class Gen:
	def __init__(self):
		pass

	def __call__(self):
		s = conf.L2socket()
		one_byte = b'\xff'
		start=time.time()
		for i in range(10000):
			pkt = Ether() / IP(dst="192.168.64.1") / TCP(sport=1234) / (
						one_byte * 1400)
			print(len(pkt))
			s.send(pkt)
		end=time.time()
		print("used time :{} s".format(end-start))

if __name__ == '__main__':
	generator=Gen()
	generator()
