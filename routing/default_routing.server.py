import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from utils.common_utils import is_digit, info,debug
from sockets.server import Server
import random
import networkx as nx
from itertools import islice

nodes=9
K=3
g:nx.Graph=nx.grid_graph([3,3])
g=nx.relabel_nodes(g,lambda x:x[0]*K+x[1])

def k_shortest_paths(G, source, target, k, weight=None):
	return list(islice(nx.shortest_simple_paths(G, source, target, weight=weight), k))

ksps=[]
for i in range(g.number_of_nodes()):
	for j in range(g.number_of_nodes()):
		if i==j:continue
		ksps.append(k_shortest_paths(g,i,j,K))

ksps.extend(ksps)
debug("ksp calculated")

class DumbHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		res=[]
		for i in range(nodes*(nodes-1)*2):
			res.append(ksps[i][0])
		res={"res":res}
		self.request.sendall(bytes(json.dumps(res),"utf-8"))

if __name__ == '__main__':
    port=10000
    server=Server(port,DumbHandler)
    server.start()