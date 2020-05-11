import os
from typing import List,Dict
from topo.distributed.frontend_utils import generate_host_ip
import loguru
from utils.common_utils import load_json
import subprocess
from topo.distributed.frontend_utils import status,now

logger=loguru.logger

def setup_ditg_receiver(swid:str,logfile):
    '''
    make sure logfile is complete path
    '''
    host="h{}".format(swid)
    os.system("ip netns exec {} nohup ITGRecv -l {}".format(host,swid))

valid_traffic_type=["iot","video","vr"]
class TrafficManager:
    def __init__(self,config:Dict[str,str]):
        super().__init__()
        self.id=int(config["id"])
        self.config:Dict[str,str]=config
        
        '''
        start from 1
        '''
        self.switches:List[int]=config["workers"][self.id]
        # switch->worker id
        self.remote_switches:dict[str][int]={}
        for idx,switches in enumerate(config["workers"]):
            if self.id==int(idx):continue;

            for s in switches:
                self.remote_switches[s]=idx
        self.traffic_dir:Dict[str,str]=config["traffic_dir"]
        # assert traffic type is valid
        for t in self.traffic_dir.keys():
            assert t in valid_traffic_type
       
        self.traffic:Dict[str,Dict]={}
        self._compile_traffic()
        self.traffic_history:Dict[str,str]={}

    #generate traffic configuration dict 
    #traffic id -> traffic configuration
    #traffic id=traffic_type-id

    #traffic configuration
    #{
    #    "id"  "size" "dts file" "ps file"
    # }
    def _compile_traffic(self):
        # logger.debug("Starting compile traffic information")
        # for traffic_type,directory in self.traffic_dir.items():
        #     logger.debug("compile {} in {}".format(traffic_type,directory))
        #     statictics=load_json(os.path.join(directory,"statistics.json"))

        #     self.traffic[traffic_type]=statictics
        # TODO 
        pass
    

    def generate_traffic(self,s1_id:str,s2_id:str,traffic_id:str):
        '''
        traffic_id="{}-{}".format(traffic_type,traffic_id)
        '''
        #check parameter validity
        invalid_param_error=(status.parameter_invalid,"invalid traffic_id {}".format(traffic_id))
        parameters=traffic_id.split("-")
        if len(parameters)!=2:
            return invalid_param_error
        if parameters[0] not in valid_traffic_type:
            return invalid_param_error

        #try to find traffic configuration
        if traffic_id not in self.traffic.keys():
            return status.resource_not_found,"cannot find traffic configuration with id {}".format(traffic_id)


        h1_ip=generate_host_ip(s1_id)
        h2_ip=generate_host_ip(s2_id)
        logger.info("Start sending traffic from {} to {}".format(h1_ip,h2_ip))
        traffic_conf=self.traffic[traffic_conf]

        self._do_generate_traffic(self,h1_ip,h2_ip,traffic_conf["dts"],traffic_conf["ps"])
        key="{}-{}".format(h1_ip,h2_ip)
        self.traffic_history[now()]=traffic_id

        logger.info("sending traffic from {} to {} done".format(h1_ip,h2_ip))


    def _do_generate_traffic(self,src_ip,dst_ip,dts_file,ps_file):
        '''
        TODO asynchoronous traffic generate
        '''
        pass

    
    def _setup_ditg_receiver(self):
        for swid in self.switches:
            setup_ditg_receiver()



