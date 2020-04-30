from utils.common_utils import load_json,save_json,save_pkl
from typing import Tuple,Dict,DefaultDict,List
from utils.common_utils import check_file,check_dir
import numpy as np
import random
import os
import subprocess
from time import sleep
from utils.common_utils import debug
from multiprocessing import Process
def run(commands):
    return subprocess.run(commands)

def start_new_process_and_run(commands):
    p=Process(target=run,args=[commands])
    p.start()


def possion_interval_generator(mean:float):
    return lambda :np.random.exponential(1/mean)


class DITGGen:
    def __init__(self,stats_file,ditg_dir,self_ip,dst_ips):
        check_file(stats_file)
        self.stats=load_json(stats_file)

        check_dir(ditg_dir)
        self.ditg_dir=ditg_dir
        self.interval_generator=possion_interval_generator(50)
        self.ip=self_ip
        self.dst_ips=dst_ips

    def start(self):
        flows:List[Dict]=self.stats["flows"]
        print(len(flows))
        dst_ips=self.dst_ips
        counter=0
        while True:
            if counter>10:
                break
            counter+=1
            dst_port=random.randint(1025,65534)
            commands=[]
            dst_ip=random.sample(dst_ips,1)[0]
            flow=random.sample(flows,1)[0]
            pkts=flow["num_pkt"]
            proto=flow["proto"]
            idt=os.path.join(self.ditg_dir,flow["idt"])
            ps=os.path.join(self.ditg_dir,flow["ps"])
            commands.extend(["ITGSend","-a",dst_ip,"-Fs",ps,"-Ft",idt,"-T",proto,"-rp",dst_port,"-z",pkts])
            commands=list(map(str,commands))
            debug("run ditg commands "," ".join(commands))
            start_new_process_and_run(commands)
            debug("sleeping")
            sleep(self.interval_generator())



if __name__ == '__main__':
    dst_ips=["192.168.64.3"]
    self_ip="192.168.64.5"
    stats_file="/home/ubuntu/temp/ditgs/statistics.json"
    ditg_dir="/home/ubuntu/temp/ditgs"
    generator=DITGGen(stats_file,ditg_dir,self_ip,dst_ips)
    generator.start()
