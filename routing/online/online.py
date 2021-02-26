from utils.log_utils import debug, info, err
from routing.online.models import *
from common.graph import NetworkTopo
from utils.file_utils import load_pkl, load_json
from path_utils import get_prj_root
import os

flattened_idxes = {}
idx_to_srcdst = []
idx = 0
src_dsts = []
for i in range(66):
	for j in range(66):
		if i == j: continue
		flattened_idxes[(i, j)] = idx
		src_dsts.append((i, j))
		idx += 1


class Online:
	def __init__(self, network: NetworkTopo):
		self.network = network
		self.beta = 1
		self.K = 3
		self.src_dsts = src_dsts
		self.ksp = {}
		self._ksp()
		# init w
		for u, v, d in self.network.g.edges(data=True):
			cap = self.network.get_edge_attr(u, v, "capacity")
			self.network.add_edge_attr(u, v, "w", 1 / cap)

	def _ksp(self):
		for s, d in self.src_dsts:
			self.ksp[(s, d)] = self.network.ksp(s, d, self.K)

	def __call__(self, inpt: RoutingInput) -> RoutingOutput:
		output: RoutingOutput = None
		res = [0 for _ in range(100 * 99)]
		ksps = self.ksp
		traffic = inpt.traffic
		for traffic_idx, traffic in enumerate(traffic):
			s, d = ksps[traffic_idx]
			min_sum_w = 1e10
			min_sum_idx = 0
			for path_idx, path in enumerate(ksps[(s, d)]):
				sum_w = 0
				for u, v in zip(path[:-1], path[1:]):
					sum_w += self.network.get_edge_attr(u, v, "w")
				if sum_w < min_sum_w:
					min_sum_idx = path_idx
					min_sum_w = sum_w
			res[traffic_idx] = min_sum_idx

			# update w
			routing_path = ksps[(s, d)][min_sum_idx]
			for u, v in zip(routing_path[:-1], routing_path[1:]):
				cap = self.network.get_edge_attr(u, v, "capacity")
				old_w = self.network.get_edge_attr(u, v, "w")
				new_w = old_w * (1 + traffic / cap)
				self.network.add_edge_attr(u, v, "w", new_w)

		output = RoutingOutput(labels=res)
		return output


if __name__ == '__main__':
	topos = []
	for t in load_pkl(os.path.join(get_prj_root(), "static/satellite_overall.pkl")):
		topos.append(t["topo"])
	network = NetworkTopo(topos[0])
	network.add_edge_attr(1, 2, "hello", "yes")
	online_router = Online(network)
	debug(network.get_edge_attr(1, 2, "hello"))
	debug(network.get_edge_attr(1, 2, "capacity"))
