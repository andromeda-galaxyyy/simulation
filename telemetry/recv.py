from scapy.all import *
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether, Dot1Q
import struct
import time


curr_count=0
pkts=[]

def handle_pkt(pkt):
    global curr_count
    curr_count+=1
    pkts.append(pkt)
    print(pkt.time)
    print("Recv {} pkts".format(curr_count))


sniff(iface="h22-eth0", filter="udp port 8888",
          prn=handle_pkt, count=0, timeout=60,started_callback=lambda :print("started"))


#验证


