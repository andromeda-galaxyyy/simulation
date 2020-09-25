import matplotlib

import numpy as np
from utils.common_utils import load_pkl, save_pkl, is_digit, file_exsit, dir_exsit
import matplotlib.pyplot as plt
import networkx as nx
from itertools import islice
import pathlib
from collections import Counter
from typing import List, Tuple, Dict
import cplex
from utils.common_utils import debug, info, err
import os
from path_utils import get_prj_root
from argparse import ArgumentParser
from tmgen.models import random_gravity_tm
from routing.instance import ILPInput, ILPOutput
import random
from copy import deepcopy

matplotlib.use('agg')
cache_dir = os.path.join(get_prj_root(), "cache")
satellite_topo_dir = os.path.join(get_prj_root(), "routing/satellite_topos")
static_dir = os.path.join(get_prj_root(), "static")


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
		pos = nx.spring_layout(g)
		nx.draw_networkx_nodes(g, pos, node_size=600)
		nx.draw_networkx_edges(g, pos, edgelist=[(u, v) for (u, v, d) in g.edges(data=True)])
		nx.draw_networkx_labels(g, pos)
		plt.axis('off')
		plt.show()

	def ksp(self, source, target, k, weight="capacity"):
		if weight == "capacity":
			return list(islice((nx.shortest_simple_paths(self.g, source, target, "weight")), k))
		return list(islice((nx.shortest_simple_paths(self.g, source, target, "delay")), k))


class ILPModel:
	def __init__(self, topo: NetworkTopo, id=0):
		self.network = topo
		self.id = id
		self.K = 3
		self.nodes = list(range(self.network.g.number_of_nodes()))
		tmp = [(s, d) for s in self.nodes for d in self.nodes]
		self.src_dsts = list(filter(lambda x: x[0] != x[1], tmp))
		self.ksp = self.__cal_ksp()
		# 流量要求 （带宽、时延）
		self.demands: List[Tuple] = None
		self.input: ILPInput = None
		self.prob: cplex.Cplex = None
		self.ijk: List[List[List[List]]] = self.__cal_ijk()

	def __build_problem(self):
		prob = cplex.Cplex()
		prob.objective.set_sense(prob.objective.sense.minimize)
		demand_num = len(self.src_dsts)
		# 决策变量2*N(N-1)
		# 0代表第一类流，1代表第二类流
		var_names = []
		for flow_idx in range(4):
			var_names.extend(
				['x{}_{}_{}'.format(flow_idx, d, k) for d in range(demand_num) for k in
				 range(self.K)])

		prob.variables.add(names=var_names, types="I" * demand_num * self.K * 4)
		prob.variables.add(obj=[1], names=["u"])
		prob.parameters.simplex.limits.iterations.set(100000)
		prob.parameters.mip.tolerances.mipgap.set(0.0008)

		self.prob = prob

	def __build_var_constraints(self):
		path_rows = []
		num_src_dsts = len(self.src_dsts)

		for flow_idx in range(4):
			for i in range(num_src_dsts):
				volume_vars = ["x{}_{}_{}".format(flow_idx, i, k) for k in range(self.K)]
				path_rows.append([volume_vars, [1 for _ in range(self.K)]])

		names = []
		for flow_idx in range(4):
			names.extend(['path{}_{}var_con'.format(flow_idx, d) for d in range(num_src_dsts)])

		self.prob.linear_constraints.add(lin_expr=path_rows,
		                                 senses="E" * num_src_dsts * 4,
		                                 rhs=[1 for _ in range(num_src_dsts * 4)],
		                                 names=names)

		# xik>=0
		# -xik<=0
		greater_than_zero = []
		constraint_names = []
		for i in range(num_src_dsts):
			for k in range(self.K):
				for flow_idx in range(4):
					greater_than_zero.append([["x{}_{}_{}".format(flow_idx, i, k)], [-1]])
					constraint_names.append("greater_than_zero_x{}_{}_{}con".format(flow_idx, i, k))

		self.prob.linear_constraints.add(
			lin_expr=greater_than_zero,
			senses="L" * num_src_dsts * self.K * 4,
			rhs=[0 for _ in range(num_src_dsts * self.K * 4)],
			names=constraint_names
		)
		# link utility constraint
		# u>0====> -u<=0
		self.prob.linear_constraints.add(
			lin_expr=[[["u"], [-1]]],
			senses="L",
			rhs=[0],
			names=["u_cons"]
		)

	def __build_constraints(self):
		info("build variable constraints")
		self.__build_var_constraints()
		info("build capacity constraints")
		self.__build_capacity_constraints()
		info("build constraints done")

	def __build_capacity_constraints(self):
		net = self.network
		num_src_dsts = len(self.src_dsts)
		ilp_input: ILPInput = self.input
		# list[0]=volume
		video_demands = ilp_input.video
		iot_demands = ilp_input.iot
		voip_demands = ilp_input.voip
		ar_demands = ilp_input.ar

		capacities = []
		for u, v, d in net.g.edges(data=True):
			capacities.append(d['capacity'])
		var_names = []
		for flow_idx in range(4):
			for d in range(num_src_dsts):
				for k in range(self.K):
					var_names.append('x{}_{}_{}'.format(flow_idx, d, k))

		capacity_rows = []
		ijk = self.ijk

		for j in range(net.g.number_of_edges()):
			coeffs = []
			for i in range(num_src_dsts):
				demand = video_demands[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][0])

			for i in range(num_src_dsts):
				demand = iot_demands[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][1])

			for i in range(num_src_dsts):
				demand = voip_demands[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][2])
			for i in range(num_src_dsts):
				demand = ar_demands[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][3])

			capacity_rows.append([var_names, coeffs])

		self.prob.linear_constraints.add(lin_expr=capacity_rows,
		                                 senses="L" * self.network.g.number_of_edges(),
		                                 rhs=capacities,
		                                 names=['capacity{}cons'.format(c) for c in
		                                        range(net.g.number_of_edges())]
		                                 )

		# build utility constraints
		varss = var_names + ["u"]
		utility_rows = []
		for j in range(net.g.number_of_edges()):
			coeffs = []
			for flow_idx, demands in enumerate(
					[video_demands, iot_demands, voip_demands, ar_demands]):
				for i in range(num_src_dsts):
					demand = demands[i]
					for k in range(self.K):
						coeffs.append(demand * ijk[i][j][k][flow_idx])

			coeffs.append(-capacities[j])
			utility_rows.append([varss, coeffs])

		self.prob.linear_constraints.add(
			lin_expr=utility_rows,
			senses='L' * self.network.g.number_of_edges(),
			rhs=[0 for _ in range(self.network.g.number_of_edges())],
			names=['utilitycons{}'.format(j) for j in range(net.g.number_of_edges())]
		)

	def __cal_ksp(self) -> Dict[Tuple, Tuple]:
		'''
		计算ksp
		:return:
		'''
		ksp_file = "ksp_{}.pkl".format(self.id)
		# ksp_file = os.path.join(cache_dir, ksp_file)
		# if pathlib.Path(ksp_file).is_file():
		# 	debug("find cached ksp for {}".format(self.id))
		# 	return load_pkl(ksp_file)
		# debug("No cache found,calculating ksp")
		net = self.network
		res = {}
		for s, d in self.src_dsts:
			large_volume_paths = net.ksp(s, d, self.K)
			low_latency_paths = net.ksp(s, d, self.K, "delay")
			res[(s, d)] = (large_volume_paths, low_latency_paths)
		save_pkl(ksp_file, res)
		return res

	def __cal_ijk(self) -> List[List[List[List]]]:
		"""
		determined for flow i ,whether edge j is in kth path
		:return:
		三维数组，每个元素为一个list，第一个表示大带宽流，第二个表示低延迟流
		"""
		net = self.network
		topo = net.g
		ijk = [[[[0, 0, 0, 0] for _ in range(self.K)] for _ in range(topo.number_of_edges())] for _
		       in
		       range(len(self.src_dsts))]
		for i, (src, dst) in enumerate(self.src_dsts):
			large_volume_paths, low_latency_paths = self.ksp[(src, dst)]
			edges = list(topo.edges(data=True))
			for j in range(topo.number_of_edges()):
				u, v, _ = edges[j]
				for k in range(self.K):
					p = large_volume_paths[k]
					if net.edge_in_path(u, v, p):
						ijk[i][j][k][0] = 1
					p = low_latency_paths[k]
					# 对于iot，voip，ar来说，ijk是一样的
					if net.edge_in_path(u, v, p):
						ijk[i][j][k][1] = 1
						ijk[i][j][k][2] = 1
						ijk[i][j][k][3] = 1
		return ijk

	def solve(self, ilp_input: ILPInput) -> ILPOutput:
		self.input = ilp_input
		self.__build_problem()
		self.__build_constraints()
		try:
			self.prob.solve()
			actions = self.prob.solution.get_values()[:-1]
			print(self.prob.solution.get_values()[-1])
			print(len(actions))
			assert len(actions) == len(self.src_dsts) * self.K * 4
			n_demand = len(self.src_dsts)
			# video,iot,voip,ar

			video_res = None
			iot_res = None
			voip_res = None
			ar_res = None
			for flow_idx in range(4):
				action = actions[flow_idx * n_demand * self.K:(flow_idx + 1) * n_demand * self.K]
				values = []
				for demand_idx in range(n_demand):
					tmp = action[demand_idx * self.K:(demand_idx + 1) * self.K]
					tmp = [round(t) for t in tmp]
					# print(tmp)
					# assert sum(tmp) == 1
					values.append(tmp.index(max(tmp)))
					if demand_idx == 0:
						video_res = values
					elif demand_idx == 1:
						iot_res = values
					elif demand_idx == 2:
						voip_res = values
					else:
						ar_res = values

			return ILPOutput(video_res, iot_res, voip_res, ar_res)
		except cplex.exceptions.CplexSolverError as exc:
			err(exc)
			return None


def test_ilp():
	topos_fn = os.path.join(cache_dir, "topo.pkl")
	topo = load_pkl(topos_fn)[0]
	n_nodes = len(topo)
	tmp = [0.001 for _ in range(66 * 65)]
	ilp_input = ILPInput(video=deepcopy(tmp), iot=deepcopy(tmp), voip=deepcopy(tmp),
	                     ar=deepcopy(tmp))
	ilp_model = ILPModel(NetworkTopo(topo))
	ilp_output = ilp_model.solve(ilp_input)




if __name__ == '__main__':
	test_ilp()
