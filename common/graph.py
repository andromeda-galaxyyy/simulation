from utils.arch_utils import get_platform

import matplotlib

if "Darwin" in get_platform():
	matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import networkx as nx
from itertools import islice
from typing import List, Tuple


class NetworkTopo:
	def __init__(self, topo: List[List[Tuple]]):
		self.g = self.__gen_graph(topo)
		self.weights = []

	# self.plot()

	def __gen_graph(self, topo: List[List[Tuple]]):
		g = nx.Graph()
		num_nodes = len(topo)
		g.add_nodes_from(list(range(num_nodes)))
		for i in range(num_nodes):
			for j in range(i + 1, num_nodes):
				if -1 in topo[i][j]: continue
				capacity, delay, loss, sc = topo[i][j]
				assert capacity >= 0
				g.add_edge(i, j, weight=4000 / capacity, capacity=capacity, delay=delay, sc=sc,
				           loss=loss)

		return g

	@staticmethod
	def edge_in_path(u, v, path: List[int]):
		if u not in path: return False
		if v not in path: return False
		return abs(path.index(u) - path.index(v)) == 1

	def plot(self):
		g = self.g
		pos = nx.spring_layout(g,k=2,iterations=100)
		# pos=nx.circular_layout(g)
		# pos=nx.multipartite_layout(g)
		nx.draw_networkx_nodes(g, pos, node_size=500)
		nx.draw_networkx_edges(g, pos, edgelist=[(u, v) for (u, v, d) in g.edges(data=True)])
		nx.draw_networkx_labels(g, pos)
		# plt.axis('off')
		plt.show()
		plt.savefig("/tmp/test.png")

	def ksp(self, source, target, k, weight="capacity"):
		if weight == "capacity":
			return list(islice((nx.shortest_simple_paths(self.g, source, target, "weight")), k))
		return list(islice((nx.shortest_simple_paths(self.g, source, target, "delay")), k))
