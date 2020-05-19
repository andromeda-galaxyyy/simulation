import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from utils.common_utils import is_digit, info,err
from sockets.server import Server,recvall
# from classify.model import Dumb
import random
import numpy as np
import time
from classify.model import DT
from path_utils import get_prj_root
import os
dt_model_dir= os.path.join(get_prj_root(),"classify/models")

dt=DT()
dt.load_model(os.path.join(dt_model_dir,"dt.pkl"))

def check(content: str):
	try:
		obj = json.loads(content)
	except JSONDecodeError:
		err("cannot decode json")
		return -1

	if "stats" not in list(obj.keys()):
		return -1
	stats = obj["stats"]
	if len(stats) != 8:
		return -1
	return stats


class DumbHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_content = str(recvall(self.request), "ascii")
		stats = check(req_content)
		if stats == -1:
			err("invalid")
			self.request.close()
			return
		obj = json.loads(req_content)
		print(obj)
		millis = int(round(time.time() * 1000))

		print("received ", millis)
		if random.random()>0.5:
			res= {"res":1 }
		else:
			res = {"res": 0}
		self.request.sendall(bytes(json.dumps(res), "ascii"))

class DTHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_content = str(recvall(self.request), "ascii")
		stats = check(req_content)
		if stats == -1:
			err("invalid")
			self.request.close()
			return
		obj = json.loads(req_content)
		stats=obj[stats]
		resp={"res":0}
		try:
			res=dt.predict([stats])
		except:
			pass
		resp["res"]=res[0]
		self.request.sendall(bytes(json.dumps(resp),"ascii"))


if __name__ == '__main__':
	server = Server(1025, DumbHandler)
	server.start()
