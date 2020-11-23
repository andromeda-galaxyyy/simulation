from scapy.all import *
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether, Dot1Q
import struct
import time

p = Ether()/Dot1Q(vlan=3)/IP(src="10.0.0.1", dst="10.0.0.2") / \
            UDP(dport=8888, sport=1500)/Raw(load="1234")
            
sendp(p, iface="h22-eth0")