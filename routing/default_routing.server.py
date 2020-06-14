import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from sockets.server import recvall
from utils.common_utils import is_digit, info, debug, load_json, load_pkl
from sockets.server import Server
import random
import networkx as nx
from itertools import islice
from path_utils import get_prj_root
from utils.common_utils import info, debug, err, file_exsit
import os


def k_shortest_paths(G, source, target, k, weight=None):
	return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))


static_dir = os.path.join(get_prj_root(), "static")
topos_pkl = os.path.join(static_dir, "satellite_overall.pkl")
topos_ = load_pkl(topos_pkl)
topos = [t["topo"] for t in topos_]

default_routing = [None for _ in range(44)]

for topo_idx in range(44):
	shortest_paths = []
	g = nx.Graph()
	g.add_nodes_from(list(range(66)))
	topo = topos[topo_idx]
	for i in range(66):
		for j in range(66):
			if i >= j: continue
			if -1 not in topo[i][j]:
				# conntected
				g.add_edge(i, j)
	for i in range(66):
		for j in range(66):
			if i == j: continue
			shortest_paths.append(nx.shortest_path(g, i, j))
	shortest_paths.extend(shortest_paths)
	default_routing[topo_idx] = shortest_paths

debug("shortest path computed done")


class DumbHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_str = str(recvall(self.request), "ascii")
		debug(req_str)
		obj = json.loads(req_str)
		topo_idx = obj["topo_idx"]
		res = {"res": default_routing[topo_idx]}
		self.request.sendall(bytes(json.dumps(res),"ascii"))


# # todo topo json format
# # capacity,delay,loss,sc
# use_default_graph = True
#
# if use_default_graph:
# 	nodes = 9
# 	K = 3
# 	g: nx.Graph = nx.grid_graph([3, 3])
# 	g = nx.relabel_nodes(g, lambda x: x[0] * K + x[1])
#


# ksps = []
# for i in range(g.number_of_nodes()):
# 	for j in range(g.number_of_nodes()):
# 		if i == j: continue
# 		ksps.append(k_shortest_paths(g, i, j, K))
#
# ksps.extend(ksps)
# debug("ksp calculated")


# class DumbHandler(socketserver.BaseRequestHandler):
# 	def handle(self) -> None:
# 		res = []
# 		for i in range(nodes * (nodes - 1) * 2):
# 			res.append(ksps[i][0])
# 		res = {"res": res}
# 		debug(res)
# 		debug("sent")
# 		self.request.sendall(bytes(json.dumps(res), "ascii"))


if __name__ == '__main__':
	port = 1028
	server = Server(port, DumbHandler)
	server.start()
