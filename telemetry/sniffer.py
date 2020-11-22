from argparse import PARSER
from itertools import count
from time import sleep

from scapy import main
from utils.process_utils import start_new_thread_and_run

from scapy import config
from telemetry.base_telemeter import BaseTelemeter
from typing import Tuple, List, Dict
from scapy.all import *
from utils.log_utils import debug, info, err
import threading
import argparse

class Sniffer:
    def __init__(self,count:int,intf:str,filter:str) -> None:
        self.pkt_count=count
        self.intf=intf
        self.filter=filter

    def __send_telemetry_packet_and_listen(self) -> Tuple[int, str]:
        sniffer_lock = threading.Lock()
        current_count = 0
        sniffer_started = False

        def sniffer_started_cbk():
            nonlocal sniffer_lock
            sniffer_lock.acquire()
            nonlocal sniffer_started
            sniffer_started = True
            debug("AsyncSniffer started and lock acquired")

        def handle_pkt(pkt):
            nonlocal current_count
            current_count += 1
            debug("Recevied pkt so far:{}".format(current_count))
            # pkt.show()
            #todo handle pkt received
            if current_count == self.pkt_count:
                debug("Received all pkts so far,release the lock")
                sniffer_lock.release()

        sniffer = AsyncSniffer(iface=self.intf, count=self.pkt_count, prn=handle_pkt,
                               started_callback=sniffer_started_cbk, filter=self.filter)
        start_new_thread_and_run(func=sniffer.start, args=())

        # wait for sniffer start
        while not sniffer_started:
            sleep(0.1)
        # sniffer started,now send pkt
        debug("Sniffer started,now send pkt")
        #todo send pkt
        debug("Telemetry pkt sent,now wait for all pkts received")
        sniffer_lock.acquire()
        debug("All returned pkts receieved")

    def start(self):
        self.__send_telemetry_packet_and_listen()
    

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--intf",type=str,help="Interface to send and listen",default="enp0s5")
    parser.add_argument("--filter",type=str,help="BPF filter",default="inbound and icmp")
    parser.add_argument("--count",type=int,help="Number of packets to received",default=5)

    args=parser.parse_args()
    sniffer=Sniffer(count=int(args.count),intf=args.intf,filter=args.filter)
    sniffer.start()
    