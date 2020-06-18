import json
from json import JSONDecodeError
import socketserver
from utils.common_utils import is_digit, info, err, debug
from sockets.server import Server, recvall,recvall2
# from classify.model import Dumb
import random
import numpy as np
import time
from classify.model import DT
from path_utils import get_prj_root
import os
from multiprocessing import Pool
import asyncio, socket

dt_model_dir = os.path.join(get_prj_root(), "classify/models")

dt = DT()


# dt.load_model(os.path.join(dt_model_dir,"dt.pkl"))

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


def dumb_calculate(stats):
	debug(stats)
	if random.random() > 0.5:
		res = 1
	else:
		res = 0
	return res


class DumbHandler(socketserver.BaseRequestHandler):
	pool = Pool(10)

	def handle(self) -> None:
		req_str=recvall2(self.request)
		if req_str=="check":
			self.request.sendall(bytes("ok","ascii"))
			return
		req_content=req_str
		# req_content = str(recvall(self.request), "ascii")
		stats = check(req_content)
		if stats == -1:
			err("Invalid request {}".format(req_content))
			self.request.close()
			return
		obj = json.loads(req_content)
		debug(obj)

		future = DumbHandler.pool.apply_async(dumb_calculate,
		                                      args=(obj["stats"],),
		                                      )

		self.request.sendall(bytes(json.dumps({"res": future.get()}), "ascii"))


class DTHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_content = str(recvall(self.request), "ascii")
		stats = check(req_content)
		if stats == -1:
			err("invalid")
			self.request.close()
			return
		resp = {"res": 0}
		try:
			res = dt.predict([stats])
		except:
			pass
		resp["res"] = res[0]
		self.request.sendall(bytes(json.dumps(resp), "ascii"))


if __name__ == '__main__':
	import argparse
	parser=argparse.ArgumentParser()
	parser.add_argument("--port",type=int,help="service listening port",default=1026)
	args=parser.parse_args()
	port=int(args.port)
	server = Server(port, DumbHandler)
	server.start()


