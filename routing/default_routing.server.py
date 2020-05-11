import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from utils.common_utils import is_digit, info, debug, load_json, load_pkl
from sockets.server import Server
import random
import networkx as nx
from routing.ksp import NetworkTopo
from itertools import islice
from path_utils import get_prj_root
from utils.common_utils import info, debug, err, file_exsit
import os

# todo topo json format
# capacity,delay,loss,sc
use_default_graph = False
g: nx.Graph = None
topo_file = os.path.join(get_prj_root(), "topo/files/topo.json")
print(topo_file)
if not file_exsit(topo_file):
	topo_file = os.path.join(get_prj_root(), "routing/topo.json")
	if not file_exsit(topo_file):
		debug("use default topo")
		use_default_graph = True

if use_default_graph:
	nodes = 9
	K = 3
	g: nx.Graph = nx.grid_graph([3, 3])
	g = nx.relabel_nodes(g, lambda x: x[0] * K + x[1])
else:
	topo = load_json(topo_file)
	net = NetworkTopo(topo)
	g = net.g


def k_shortest_paths(G, source, target, k, weight=None):
	return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))


ksps = []
for i in range(g.number_of_nodes()):
	for j in range(g.number_of_nodes()):
		if i == j: continue
		ksps.append(k_shortest_paths(g, i, j, K))

ksps.extend(ksps)
debug("ksp calculated")


class DumbHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		res = []
		for i in range(nodes * (nodes - 1) * 2):
			res.append(ksps[i][0])
		res = {"res": res}
		self.request.sendall(bytes(json.dumps(res), "ascii"))


if __name__ == '__main__':
	port = 10000
	server = Server(port, DumbHandler)
	server.start()
