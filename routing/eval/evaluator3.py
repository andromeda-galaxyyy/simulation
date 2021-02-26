from utils.file_utils import *
from utils.log_utils import debug, info, err
from typing import List, Dict, Tuple
from routing.nn3.models import *
from common.graph import NetworkTopo

cache_dir = os.path.join(get_prj_root(), "cache")
static_dir = os.path.join(get_prj_root(), "static")
ksp_obj = load_json(os.path.join(static_dir, "ksp.json"))["aksp"]
debug(len(ksp_obj))
debug(len(ksp_obj[0]))

ksps = {}
for i in range(100):
	for j in range(100):
		if i == j:
			continue
		ksps[(i, j)] = ksp_obj[i][j]

debug(ksps[(89, 23)])
debug(ksps[(10, 45)])


class RoutingEvaluator3:
	def __init__(self, topo: List[List[Tuple]], K: int = 5):
		self.topo: List[List[Tuple]] = topo
		self.k = K
		N = len(topo[0])
		self.topo = NetworkTopo(topo)
		# src_dsts = [(i, j) for i in range(N) for j in range(N)]
		src_dsts = []
		for i in range(100):
			for j in range(100):
				if i == j: continue
				src_dsts.append((i, j))
		# self.src_dsts = list(filter(lambda x: x[1] != x[0], src_dsts))
		self.src_dsts = src_dsts

		self.ksp = ksps
		self.cache: Dict = {}
		# for s, d in self.src_dsts:
		# 	large_volume_paths = self.topo.ksp(s, d, self.k)
		# 	low_latency_paths = self.topo.ksp(s, d, self.k, "delay")
		# 	self.ksp[(s, d)] = (large_volume_paths, low_latency_paths)

		debug("Routing evaluator solve ksp done")

	def __call__(self, routing: Routing) -> float:
		rv = -1
		edges = list(self.topo.g.edges(data=True))
		src_dsts = self.src_dsts
		ksp = self.ksp

		cache: Dict = self.cache
		for j in range(self.topo.g.number_of_edges()):
			utility = 0
			u, v, d = edges[j]

			for i, (src, dst) in enumerate(src_dsts):
				paths = ksp[(src, dst)]
				# video
				path = paths[routing.labels[i]]
				key = "{}-{}-{}".format(u, v, "%".join(map(str,path)))
				if key not in self.cache.keys():
					cache[key] = self.topo.edge_in_path(u, v, path)

				if cache[key]:
					utility += routing.traffic[i]

			# path = low_latency_paths[routing.labels["iot"][i]]
			# if self.topo.edge_in_path(u, v, path):
			# 	utility += routing.iot[i]
			#
			# path = low_latency_paths[routing.labels["voip"][i]]
			# if self.topo.edge_in_path(u, v, path):
			# 	utility += routing.voip[i]
			#
			# path = low_latency_paths[routing.labels["ar"][i]]
			# if self.topo.edge_in_path(u, v, path):
			# 	utility += routing.ar[i]

			rv = max(rv, utility)
		return rv


if __name__ == '__main__':
	pass
