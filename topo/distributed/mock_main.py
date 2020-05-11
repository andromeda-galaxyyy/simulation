import os
dir_path = os.path.dirname(os.path.realpath(__file__))
os.sys.path.append("/home/ubuntu/code/graduate/satellite_topo")
import argparse
from utils import load_json
from argparse import ArgumentParser

os.sys.path.append(dir_path)
from frontend.topomanager import TopoManager
from typing import List
import requests
import loguru 
logger=loguru.logger

def add(idx1,idx2,topo:List):
	topo[idx1][idx2]=[]
	topo[idx2][idx1]=[]
	topo[idx1][idx2].extend(["20ms","1mbit"])
	topo[idx2][idx1].extend(["20ms","1mbit"])

if __name__ == '__main__':
	# parser=ArgumentParser()
	# parser.add_argument("--worker",type=int)
	# args=parser.parse_args()
	# worker_id=args.worker

	topo=[[["None"] for _ in range(0,6)]for _ in range(0,6)]
	add(0,1,topo)
	add(1,2,topo)
	add(0,3,topo)
	add(1,4,topo)
	add(2,5,topo)




	config=load_json("/home/ubuntu/code/graduate/satellite_topo/frontend/mock_config.json")
	r=requests.post(url="http://localhost:5000/config",json=config)
	logger.info("post config status code {}".format(r.status_code))

	r=requests.post(url="http://localhost:5000/topo",json={"topo":topo});
	logger.info("post topo status code {}".format(r.status_code))

	r=requests.delete(url="http://localhost:5000/topo")
	logger.info("delete topo status code {}".format(r.status_code))
	r=requests.get(url="http://localhost:5000/config")
	logger.info("get topo status code {} json {}".format(r.status_code,r.json()))
	
	# config["id"]=worker_id
	# manager=TopoManager(config)

	# manager.diff_topo(topo)
	# #
	# manager.tear_down()

