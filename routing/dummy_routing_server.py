import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from sockets.server import recvall, recvall2, sendall
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


ksps = [None for _ in range(44)]
# ksps=[NH]

n_nodes = 100
static_dir = os.path.join(get_prj_root(), "static")
topos_pkl = os.path.join(static_dir, "military.pkl")
topos_ = load_pkl(topos_pkl)
topos = [t["topo"] for t in topos_]

default_routing = [None for _ in range(44)]

for topo_idx in range(44):
	topo = topos[topo_idx]
	shortest_paths = []
	g = nx.Graph()
	n_nodes = len(topo)
	debug(n_nodes)
	g.add_nodes_from(list(range(n_nodes)))
	for i in range(n_nodes):
		for j in range(n_nodes):
			if i >= j: continue
			if -1 not in topo[i][j]:
				# conntected
				g.add_edge(i, j)
	for i in range(n_nodes):
		for j in range(n_nodes):
			if i == j: continue
			# if topo_idx==0:
			# if i==99 and j==0:
			# 	debug(nx.shortest_path(g,i,j))
			shortest_paths.append(nx.shortest_path(g, i, j))

	# shortest_paths.extend(shortest_paths)
	default_routing[topo_idx] = shortest_paths
	debug("compute {} done".format(topo_idx))

debug("shortest path computed done")


class DumbHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_str = recvall2(self.request)
		debug(req_str)
		if req_str == "default":
			res = {"default": default_routing[0]}
		else:
			# video,iot,voip,ar
			res = {
				"0": default_routing[0],
				"1": default_routing[0],
				"2": default_routing[0],
				"3": default_routing[0],
			}
		debug(res)
		self.request.sendall(bytes(json.dumps(res), "ascii"))


if __name__ == '__main__':
	port = 1038
	server = Server(port, DumbHandler)
	server.start()
