from utils.log_utils import debug,info,err  
from typing import Any, List,Tuple,Dict
from sockets.client import send
import json
import time

class BaseTelemeter:
    def __init__(self,ovsids:List[int],topo:List[List[List[int]]],config:Dict) -> None:
        #本服务器上的ovsid
        self.ovsids:List[int]=ovsids
        self.topo:List[List[List[int]]]=topo
        self.config:Dict=config
        self.sniffer_config={
            "iface":"h22-eth0",
            "filter":"inbound and udp",
            "count":103
        }

    def __calculate_monitor(self,links:List[Tuple[int,int]])->int:
        # topo 的组织形式为临接矩阵，矩阵中的每个元素为一个四元素列表
        #  link [(0,1),(1,100)]
        if -1 in self.topo[0][1]:
            # 不存在
            pass
        else:
            #存在
            pass

        raise NotImplementedError

    def __calculate_flow(self,links:List[Tuple[int,int]])->Tuple[int,str,Any]:
        '''
        抽象方法，由具体的子类给出实现方式,成功返回0，错误返回-1
        （错误码,出错信息,发送给控制器的内容,务必为json)
        '''
        # if anything goes wrong,
        # return -1,"error msg",{}
        # otherwise 
        # return 0,"",{"flows":[]}
        raise NotImplementedError

    def __do_stop(self):
        raise NotImplementedError

    def __start_sniffer(self) -> Tuple[int, str]:
        '''
        send telemetry packet,return 0 if success,-1 otherwise
        str if any,indicates error message
        '''
        # if anything goes wrong,
        # return -1,"error msg"
        # otherwise
        # return 0,""
        raise NotImplementedError

    def __do_collect_stats(self) -> Tuple[int, str, Any]:
        '''
        collect link delay stats
        return 0 if success,-1 otherwise,str if any,indicates error message
       '''
        raise NotImplementedError




    def stop(self):
        debug("Stop telemeter")
        self.__do_stop()


    def start(self,links:List[Tuple[int,int]]):
        # 计算monitor
        monitor_id=self.__calculate_monitor(links)
        # 如果monitor不在本服务器上,返回
        if monitor_id not in self.ovsids:
            debug("Noting todo on this server,return")
            return

        debug("Monitory calculated")
        debug("Start to calculate flow rules")
        ret_code,msg,obj=self.__calculate_flow(links)
        if ret_code!=0:
            err("Error when calculate flow,msg:{}".format(msg))
            return
        debug("Calculate flow successfully")
        # send to controller
        debug("Start to send to controller")
        controller_ip=self.config["controller"]
        controller_telemetry_port=int(self.config["controller_telemetry_port"])
        send(controller_ip,controller_telemetry_port,json.dumps(obj)+"*")
        debug("Flow rules sent to controller")
        # sleep for 10 seconds,wait for flow rules to be installed
        time.sleep(10)
        # send telemetry_packet and listen
        debug("Wake up from 10-seconds sleep")
        debug("Start to send telemetry packet")
        ret_code,msg=self.__start_sniffer()
        if ret_code!=0:
            err("Error when send telemetry_packet and listen {}".format(self.msg))
            return
        
        debug("Telemetry work done")

    def collect_stats(self)->Any:
        debug("Start to collect stats")
        ret_code,msg,obj=self.__do_collect_stats()
        if ret_code!=-1:
            err("Error when collect stats {}".format(msg))
            return 
        
        #todo what to do with stats
        
        

    

