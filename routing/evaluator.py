from utils.file_utils import *
from utils.log_utils import debug, info, err
from typing import List, Dict, Tuple
from routing.instance import *
from common.Graph import NetworkTopo


class RoutingEvaluator:
	def __init__(self, topo: List[List[Tuple]], K: int):
		self.topo: List[List[Tuple]] = topo
		self.k = K
		N = len(topo[0])
		self.topo = NetworkTopo(topo)
		src_dsts = [(i, j) for i in range(N) for j in range(N)]
		self.src_dsts = list(filter(lambda x: x[1] != x[0], src_dsts))

		self.ksp = {}

		for s, d in self.src_dsts:
			large_volume_paths = self.topo.ksp(s, d, self.k)
			low_latency_paths = self.topo.ksp(s, d, self.k, "delay")
			self.ksp[(s, d)] = (large_volume_paths, low_latency_paths)

	def __call__(self, routing: RoutingInstance) -> float:
		rv = -1
		edges = list(self.topo.g.edges(data=True))
		src_dsts = self.src_dsts
		ksp = self.ksp

		for j in range(self.topo.g.number_of_edges()):
			utility = 0
			u, v, d = edges[j]

			for i, (src, dst) in enumerate(src_dsts):
				large_volume_paths, low_latency_paths = ksp[(src, dst)]
				# video
				path = large_volume_paths[routing.labels["video"][i]]
				if self.topo.edge_in_path(u, v, path):
					utility += routing.video[i]

				path = low_latency_paths[routing.labels["iot"][i]]
				if self.topo.edge_in_path(u, v, path):
					utility += routing.iot[i]

				path = low_latency_paths[routing.labels["voip"][i]]
				if self.topo.edge_in_path(u, v, path):
					utility += routing.voip[i]

				path = low_latency_paths[routing.labels["ar"][i]]
				if self.topo.edge_in_path(u, v, path):
					utility += routing.ar[i]

			rv = max(rv, utility / 100)
		return rv
