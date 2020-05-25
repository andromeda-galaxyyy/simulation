import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from utils.common_utils import is_digit, info, debug
from sockets.server import Server, recvall
import random
import networkx as nx
from itertools import islice
import time
from datetime import datetime

nodes = 9
K = 3
g: nx.Graph = nx.grid_graph([3, 3])
g = nx.relabel_nodes(g, lambda x: x[0] * K + x[1])


def k_shortest_paths(G, source, target, k, weight=None):
	return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))


ksps = []
for i in range(g.number_of_nodes()):
	for j in range(g.number_of_nodes()):
		if i == j: continue
		ksps.append(k_shortest_paths(g, i, j, K))

ksps.extend(ksps)

debug("ksp calculated")


def check(content: str):
	try:
		obj = json.loads(content)
	except JSONDecodeError:
		return -1
	if "volumes" not in list(obj.keys()):
		return -1
	volumes = obj["volumes"]
	if len(volumes) != nodes * (nodes - 1) * 2:
		return -1

	return volumes


class DumbHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_str = str(recvall(self.request), "ascii")
		vols = check(req_str)
		if vols == -1:
			return
		l = len(vols)
		print(vols)
		now = datetime.now()

		current_time = now.strftime("%H:%M:%S")
		print(current_time)
		res = []
		for i in range(l):
			randidx = random.randint(0, K - 1)
			res.append(ksps[i][randidx])
		res = {"res": res}
		self.request.sendall(bytes(json.dumps(res), "ascii"))

class DumbHandlerWithDumbModel(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		pass

if __name__ == '__main__':
	port = 1027
	server = Server(port, DumbHandler)
	server.start()
