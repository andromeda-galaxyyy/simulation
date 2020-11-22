from itertools import count
from time import sleep
from utils.process_utils import start_new_thread_and_run

from scapy import config
from telemetry.base_telemeter import BaseTelemeter
from typing import Tuple,List,Dict
from scapy.all import *
from utils.log_utils import debug,info,err
import threading


class Telemeter(BaseTelemeter):
    def __send_telemetry_packet_and_listen(self) -> Tuple[int, str]:
        sniffer_lock=threading.Lock()
        current_count=0
        sniffer_started=False
        def sniffer_started_cbk():
            sniffer_lock.acquire()
            sniffer_started=True
            debug("AsyncSniffer started and lock acquired")

        def handle_pkt(pkt):
            current_count+=1
            debug("Recevied pkt so far:{}".format(current_count))
            #todo handle pkt received
            if current_count==self.config["count"]:
                debug("Received all pkts so far")
                sniffer_lock.release()

        sniffer=AsyncSniffer(iface=self.sniffer_config["iface"],count=self.num_pkt,prn=handle_pkt,started_callback=sniffer_started_cbk,filter=self.sniffer_config["filter"])
        start_new_thread_and_run(func=sniffer.start,args=())

        # wait for sniffer start
        while not sniffer_started:
            sleep(0.1)
        # sniffer started,now send pkt
        debug("Sniffer started,now send pkt")
        #todo send pkt
        debug("Telemetry pkt sent,now wait for all pkts received")
        sniffer_lock.acquire()
        debug("All return pkts receieved")



