from itertools import count
from os import kill
from time import process_time, sleep
from utils.process_utils import run_ns_process_background, run_process_background, start_new_thread_and_run
from utils.process_utils import kill_pid

from scapy import config
from telemetry.base_telemeter import BaseTelemeter
from typing import Tuple,List,Dict
from scapy.all import *
from utils.log_utils import debug,info,err
import threading


class Telemeter(BaseTelemeter):
    def __start_sniffer(self) -> Tuple[int, str]:
        command="python ./telemetry/sniffer.py --count {} --intf {} --filter {}".format(self.sniffer_config["count"],self.sniffer_config["iface"],self.sniffer_config["filter"])
        pid=run_ns_process_background(ns=self.sniffer_config["namespace"],command=command)
        self.sniffer_pid=pid
    
    def __do_stop(self):
        kill_pid(self.sniffer_pid)
    







