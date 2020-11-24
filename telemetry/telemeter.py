from itertools import count
from os import kill
from time import process_time, sleep
from utils.process_utils import run_ns_process_background, run_process_background, start_new_thread_and_run
from utils.process_utils import kill_pid
from path_utils import get_prj_root
from scapy import config
from telemetry.base_telemeter import BaseTelemeter
from typing import Tuple,List,Dict
from scapy.all import *
from utils.log_utils import debug,info,err
import threading
from typing import List,Any
from utils.file_utils import load_pkl
from utils.file_utils import load_json
from telemetry.base_telemeter import BaseTelemeter
from utils.log_utils import debug,info


class Telemeter(BaseTelemeter):
    def _start_sniffer(self) -> Tuple[int, str]:
        command="python ./telemetry/sniffer.py --count {} --intf {} --filter '{}'".format(
            self.sniffer_config["count"],
            self.sniffer_config["iface"],
            self.sniffer_config["filter"])
        pid=run_ns_process_background(ns=self.sniffer_config["namespace"],command=command,output="/tmp/sniffer.log")
        self.sniffer_pid=pid
        debug("started subprocess pid {}".format(pid))
        return 0,""
    
    def _do_stop(self):
        kill_pid(self.sniffer_pid)

    def _calculate_monitor(self, links: List[Tuple[int, int]]) -> Tuple[int,str,int]:
        return 0,"",22

    def _calculate_flow(self, links: List[Tuple[int, int]]) -> Tuple[int, str, Any]:
        return 0,"",load_json(os.path.join(get_prj_root(),"telemetry/default_flows.json"))

    def _do_collect_stats(self) -> Tuple[int, str, Any]:
        return 0,"",load_pkl("/tmp/telemetry.link.pkl")








