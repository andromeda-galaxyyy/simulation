from os.path import pardir
from path_utils import get_prj_root
from utils.log_utils import debug,info,err,warn
from utils.arch_utils import get_platform
from utils.file_utils import read_lines
import argparse
import matplotlib 
if "Darwin" in get_platform():
    matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from collections import namedtuple
from typing import Dict,List,Tuple,NamedTuple
DelayInstance=namedtuple("DelayInstance",field_names=["min","max","mean","std","label"])
LossInstance=namedtuple(typename="LossInstance",field_names=["loss","label"])


#delay
# 5ms
# 10ms 
# 20ms 
# 50ms

#loss 
#0.1 0.2 0.4 0.6

import os
delay_dirs=["/tmp/rxdelay_5","/tmp/rxdelay_10","/tmp/rxdelay_20","/tmp/rxdelay_50"]
delay_true=[5,10,20,50]
loss_dirs=["/tmp/rxloss_1","/tmp/rxloss_2","/tmp/rxloss_4","/tmp/rxloss_6"]
loss_true=[0.1,0.2,0.4,0.6]

# boxplot 四合一
# 每个delay一张图
# https://matplotlib.org/3.1.1/gallery/statistics/boxplot_demo.html
def plot_delay(delay_instances:List[DelayInstance],fn="/tmp/delay.png"):
    pass

# boxplot 四合一
# 每个loss一张图
def plot_loss(loss_instances:List[LossInstance],fn="/tmp/loss.png"):

    pass

def load()->Tuple[List[DelayInstance],List[LossInstance]]:
    delay_instances:List[DelayInstance]=[]
    loss_instances:List[LossInstance]=[]
    for idx,delay_label in enumerate([5,10,20,50]):
        dirt=delay_dirs[idx]
        for fn in os.listdir(dirt):
            if ".delay" not in fn:continue
            fn=os.path.join(dirt,fn)
            debug("load file {}".format(fn))
            lines=read_lines(fn)
            lines=lines[1:]

            #RxStartTs RxEndTs sip sport dip dport proto min max mean stdvar flowtype 
            # 1611192411748 1611192414687 10.0.0.1 13941 10.0.0.2 44292 UDP 0 1 0.04 0.19 0 
            for l in lines:
                content=l.split(" ")
                delay_instances.append(DelayInstance(min=content[-5],max=content[-4],mean=content[-3],std=content[-2],label=delay_label))
    
    for idx,loss_label in enumerate([0.1,0.2,0.4,0.6]):
        dirt=loss_dirs[idx]
        for fn in os.listdir(dirt):
            if ".loss" not in fn:continue
            fn=os.pardir.join(dirt,fn)
            debug("load file {}".format(fn))
            lines=read_lines(fn)
            lines=lines[1:]
            for l in lines:
                content=l.split(" ")
                # 1611193179817 0 88 0.12 10.0.0.1 13941 10.0.0.2 44292 UDP 0 
                loss_instances.append(LossInstance(label=loss_label,loss=content[3]))
    return delay_instances,loss_instances


            
    
    
            
            
        







if __name__ == "__main__":
    delay_instances,loss_instances=load()
    plot_delay(delay_instances)
    plot_loss(loss_instances)
    # parser=argparse.ArgumentParser()
    # parser.add_argument("--loss_dir","/tmp/rxloss")
    # parser.add_argument("--delay_dir","/tmp/rxdelay")
    # args=parser.parse_args()

