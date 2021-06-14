from networkx.exception import PowerIterationFailedConvergence
from utils.time_utils import now_in_milli
from networkx.algorithms.coloring.greedy_coloring import strategy_connected_sequential
from utils.log_utils import debug, info, err
from routing.online.models import *
from common.graph import NetworkTopo
from utils.file_utils import load_pkl, load_json
from path_utils import get_prj_root
import os
import numpy as np
from sockets.server import Server
from sockets.server import recvall2
import socketserver
from typing import List,Dict,Tuple

model_static_dir = os.path.join(get_prj_root(), "routing/nn2.1/static")
models = {}
# readypaths = load_json(os.path.join(model_static_dir, "ready114paths.json"))
# indexofmodelin = load_json(os.path.join(model_static_dir, "linkpairofpath.json"))
ksps_tmp = load_json(os.path.join(get_prj_root(), "static/ksp.json"))["aksp"]
# debug(len(ksps_tmp))
# debug(len(ksps_tmp[0]))
flattern_idx={}
ksps = []
src_dsts=[]
idx=0
for i in range(100):
	for j in range(100):
		if i == j:
			continue
		ksps.append(ksps_tmp[i][j])
		src_dsts.append((i,j))
		flattern_idx[(i,j)]=idx
		idx+=1
		

assert len(ksps[0]) == 5
debug(ksps[0][4])
assert len(ksps) == 100 * 99


class Online:
	def __init__(self, network: NetworkTopo):
		self.network = network
		self.beta = 1
		self.K = 3
		self.src_dsts = src_dsts
		self.ksp = ksps
		# self._ksp()
		debug("online algorithm solve ksp done")
		# init w
		for u, v, d in self.network.g.edges(data=True):
			cap = self.network.get_edge_attr(u, v, "capacity")
			self.network.add_edge_attr(u, v, "w", 1 / cap)

	def _ksp(self):
		for s, d in self.src_dsts:
			self.ksp[(s, d)] = self.network.ksp(s, d, self.K)

	def reset(self):
		for u, v, d in self.network.g.edges(data=True):
			cap = self.network.get_edge_attr(u, v, "capacity")
			self.network.add_edge_attr(u, v, "w", 1 / cap)

	def __call__(self, inpt: List[int]):
		res = [0 for _ in range(100 * 99)]
		ksps = self.ksp
		traffic = inpt
		res_paths=[]
		for traffic_idx, traffic in enumerate(traffic):
			s, d = src_dsts[traffic_idx]
			min_sum_w = 1e10
			min_sum_idx = -1
			for path_idx, path in enumerate(ksps[traffic_idx]):
				sum_w = 0
				for u, v in zip(path[:-1], path[1:]):
					sum_w += self.network.get_edge_attr(u, v, "w")
				if sum_w < min_sum_w:
					min_sum_idx = path_idx
					min_sum_w = sum_w
			res[traffic_idx] = min_sum_idx

			# update w
			routing_path = ksps[traffic_idx][min_sum_idx]
			# debug(routing_path)
			res_paths.append(routing_path)
			# debug(routing_path[1])
			# debug(routing_path)
			for u, v in zip(routing_path[:-1], routing_path[1:]):
				cap = self.network.get_edge_attr(u, v, "capacity")
				old_w = self.network.get_edge_attr(u, v, "w")
				new_w = old_w * (1 + traffic / cap)
				self.network.add_edge_attr(u, v, "w", new_w)
		self.reset()
		return res_paths

import json
static_dir=os.path.join(get_prj_root(),"static")


topo=load_json(os.path.join(static_dir,"topo.json"))["topo"]
# topo=json.load(os.path.join(static_dir,"topo.json"))

topo=NetworkTopo(topo)

online_router=Online(topo)

class handler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req = recvall2(self.request)
		req = json.loads(req)
		# rate = req["rate"]
		matrix = req["matrix"]["0"]
		# debug(req)

		start = now_in_milli()
		paths=online_router(matrix)
		with open("/tmp/online.time","a+") as fp:
			consume=now_in_milli()-start
			fp.write("{}\n".format(consume))
			fp.flush()

		debug("routing computing cost {} milliseconds".format(now_in_milli()-start))

		res = {
			"res1": paths
		}
		self.request.sendall(bytes(json.dumps(res) + "*", "ascii"))




if __name__ == '__main__':
	matrix=[1 for _ in range(100*99)]
	paths=online_router(matrix)
	debug(len(paths))
	for i in range(100):
		for j in range(100):
			if i==j:continue
			path=paths[flattern_idx[(i,j)]]
			assert path[0]==i
			assert path[-1]==j
			
	debug(paths[flattern_idx[(10,9)]])
	debug(paths[flattern_idx[(10,99)]])

	port=1055
	server=Server(port,handler)
	server.start()



