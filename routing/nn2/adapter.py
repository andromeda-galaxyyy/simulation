from utils.log_utils import info, err, debug, warn
from utils.file_utils import load_pkl, load_json, save_json
import os
from path_utils import get_prj_root
from utils.file_utils import static_dir
from socketserver import BaseRequestHandler
from sockets.server import recvall2, Server
from typing import Dict, List, Tuple
import json
from threading import Thread
import socket

from routing.nn2.dummy_model import DummyModel


class SingleModelAdapter:
	def __init__(self,model_key:str,addr:str):
		self.addr=addr
		self.model_key=model_key
		self.server=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
		self.server.bind(self.addr)
		#todo
		self.model=DummyModel()


	def start(self):
		self.server.listen()
		debug("Single server  {} started".format(self.model_key))
		while True:
			conn,_=self.server.accept()
			debug("new connection")
			req=recvall2(conn)
			debug("received done {}".format(req))
			debug(req)
			req=json.loads(req)
			rates=req["rates"]
			debug("rates {}".format(rates))
			# output=self.model(rates)
			res={"res":self.model(rates)}
			conn.sendall(bytes(json.dumps(res)+"*","ascii"))
			conn.close()


if __name__ == '__main__':
	os.system("rm /tmp/0-1.sock")
	adapter=SingleModelAdapter("0-1","/tmp/0-1.sock")
	adapter.start()
