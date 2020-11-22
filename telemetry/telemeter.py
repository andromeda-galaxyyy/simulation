from itertools import count
from time import process_time, sleep
from utils.process_utils import run_ns_process_background, run_process_background, start_new_thread_and_run

from scapy import config
from telemetry.base_telemeter import BaseTelemeter
from typing import Tuple,List,Dict
from scapy.all import *
from utils.log_utils import debug,info,err
import threading


class Telemeter(BaseTelemeter):
    def __start_sniffer(self) -> Tuple[int, str]:
        command="python ./telemetry/sniffer.py --count {} --intf {} --filter {}".format(self.sniffer_config["count"],self.sniffer_config["iface"],self.sniffer_config["filter"])
        run_process_background(command=command)
    
    



