import json
from json import JSONDecodeError
import socketserver

from networkx.exception import NetworkXUnfeasible
from utils.log_utils import debug, info, err
from sockets.server import Server, recvall2
from common.graph import NetworkTopo
from utils.file_utils import load_pkl, load_json
from routing.nn3.models import *
from utils.time_utils import now_in_milli
from utils.log_utils import debug
from typing import List, Tuple, Dict
from routing.nn3.contants import *
from path_utils import get_prj_root
import os

# loading ksps

# cache_dir = os.path.join(get_prj_root(), "cache")
# static_dir = os.path.join(get_prj_root(), "static")
# ksp_obj = load_json(os.path.join(static_dir, "ksp.json"))["aksp"]
#
# ksps = {}
# for i in range(100):
# 	for j in range(100):
# 		if i == j:
# 			continue
# 		ksps[(i, j)] = ksp_obj[i][j]


from threading import Thread
import socket


class Predictor:
	def __init__(self):

		pass

	def _fetch_single_routing(self, model_id, traffic: List[float], res: List[int]):
		sock_fn = os.path.join("/tmp/{}.sock".format(model_id))
		client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			client.connect(sock_fn)
		except socket.error as msg:
			err(msg)
			exit(-1)
		req = {
			"volumes": traffic
		}
		client.sendall(bytes(json.dumps(req) + "*", "ascii"))
		try:
			resp = recvall2(client)
		finally:
			client.close()
		resp = json.loads(resp)
		actions = resp["actions"]
		n_action = len(modelid_to_targets[model_id])
		actions = actions[:n_action]
		for idx, target in enumerate(modelid_to_targets[model_id]):
			action = actions[idx]
			flattened_idx = flattenidxes[(model_id, target)]
			res[flattened_idx] = action

	def __call__(self, inpt: RoutingInput):
		traffic = inpt.traffic
		res = [0 for _ in range(100 * 99)]
		threads = []
		for model_id in modelid_to_targets.keys():
			t = Thread(target=self._fetch_single_routing, args=(model_id, traffic, res))
			t.start()
			threads.append(t)
		for t in threads:
			t.join()
		out = RoutingOutput(labels=res)
		return out


predictor = Predictor()


class NN3Server(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_content = recvall2(self.request)
		obj: Dict = {}
		try:
			obj = json.loads(req_content)
		except JSONDecodeError as e:
			err(obj)

		routing: RoutingOutput = predictor(obj["matrix"])
		paths = []
		for i in range(100):
			for j in range(100):
				if i == j: continue
				paths.append(ksps[routing.labels[flattenidxes[(i, j)]]])

		res = {"res1": paths}
		self.request.sendall(bytes(json.dumps(res) + "*", "ascii"))


if __name__ == '__main__':
	port = 1055
	server = Server(port, NN3Server)
	debug("nn routing server started")
	server.start()
