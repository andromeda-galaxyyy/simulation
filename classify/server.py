import json
from json import JSONDecodeError
import socketserver
from utils.common_utils import is_digit, info, err, debug
from sockets.server import Server, recvall, recvall2
# from classify.model import Dumb
import multiprocessing
import random
import numpy as np
import time
from classify.model import DT
from path_utils import get_prj_root
import os
from multiprocessing import Pool
import asyncio, socket

dt_model_dir = os.path.join(get_prj_root(), "classify/models")
dt_model_pkl = os.path.join(dt_model_dir, "dt.pkl")

num_process = 20
dt = DT()
dts = [None for _ in range(num_process)]

for idx in range(num_process):
	dts[idx] = DT()
	dts[idx].load_model(dt_model_pkl)
	debug("{}th process loaded model".format(idx))


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
	# pool = Pool(num_process)
	pool=None

	def handle(self) -> None:
		req_str = recvall2(self.request)
		if req_str == "check":
			self.request.sendall(bytes("ok", "ascii"))
			return
		req_content = req_str
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


def dt_calculated(stats):
	global dts
	pid = os.getpid()
	# proc=multiprocessing.current_process.
	model = dts[pid % num_process]
	return int(model.predict([stats])[0])


class DTHandler(socketserver.BaseRequestHandler):
	pool = Pool(num_process)

	def handle(self) -> None:
		req_content = recvall2(self.request)
		if req_content == "check":
			self.request.sendall(bytes("ok", "ascii"))
			return
		stats = check(req_content)
		if stats == -1:
			err("invalid")
			self.request.close()
			return
		resp = {"res": 0}

		future = DTHandler.pool.apply_async(dt_calculated, args=(stats,))
		resp["res"] = future.get()
		self.request.sendall(bytes(json.dumps(resp), "ascii"))


if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("--port", type=int, help="service listening port", default=1040)
	args = parser.parse_args()
	port = int(args.port)
	server = Server(port, DTHandler)
	server.start()
