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
from threading import Thread

from path_utils import get_prj_root
bin_dir=os.path.join(get_prj_root(),"traffic/ditg/bin")

def run(commands):
    return subprocess.run(commands)

def start_new_process_and_run(commands):
    p=Process(target=run,args=[commands])
    p.start()
    # print(p.pid)
    # sleep(1)
    # subprocess.run(["lsof","-i","-P","|","grep",str(p.pid)])
    # os.system("lsof -i -P|grep {}".format(p.pid))


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

    def stop(self):
        #todo stop traffic generator,kill all child process
        pass


class IperfGen:
    def __init__(self,src_ip,dst_ips):
        pass


class DummyGen:
    def __init__(self,lambada,self_ip,dst_ips):
        self.interval_generator=possion_interval_generator(lambada)
        self.ip=self_ip
        self.dst_ips=dst_ips

    @staticmethod
    def bin_runner(commands):
        subprocess.run(commands)

    def start(self):
        sender_bin = os.path.join(bin_dir,"ITGSend")
        dst_ips=self.dst_ips
        while True:
            target=random.choice(dst_ips)
            print("target ip: ",target)
            src_port=random.randint(1500,65534)
            src_port=str(src_port)
            dst_port=random.randint(1500,65534)
            dst_port=str(dst_port)
            sig_port=str(random.choice(["1030","1031","1032"]))

            commands=[sender_bin,"-a",target,"-Sdp",sig_port,"-sp",src_port,"-rp",dst_port,"-t","100"]
            thread = Thread(target=DummyGen.bin_runner, args=(commands,))
            thread.start()
            sleep(self.interval_generator())




if __name__ == '__main__':
    dst_ips=["127.0.0.1"]
    self_ip="127.0.0.1"
    stats_file="/home/ubuntu/temp/ditgs/statistics.json"
    ditg_dir="/home/ubuntu/temp/ditgs"
    generator=DummyGen(10,self_ip,dst_ips)
    generator.start()
