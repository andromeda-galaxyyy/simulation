import matplotlib

matplotlib.use('agg')
from utils.common_utils import load_pkl, save_pkl, save_json
import matplotlib.pyplot as plt
import networkx as nx
from itertools import islice
import pathlib
import random
from collections import Counter
from typing import List, Tuple, Dict, DefaultDict
import cplex
from utils.common_utils import debug, info, err
import os
from path_utils import get_prj_root

cache_dir = os.path.join(get_prj_root(), "cache")


class NetworkTopo:
	def __init__(self, topo: List[List[List]]):
		self.g = self.__gen_graph(topo)
		self.weights = []

	# self.plot()

	def __gen_graph(self, topo: List[List[Tuple]]):
		g = nx.Graph()
		num_nodes = len(topo)
		g.add_nodes_from(list(range(num_nodes)))
		for i in range(num_nodes):
			for j in range(i + 1, num_nodes):
				if topo[i][j] is None: continue
				capacity, delay, sc = topo[i][j]
				assert capacity >= 0
				g.add_edge(i, j, weight=4000 / capacity, capacity=capacity, delay=delay, sc=sc)

		return g

	@staticmethod
	def edge_in_path(u, v, path: List[int]):
		if u not in path: return False
		if v not in path: return False
		return abs(path.index(u) - path.index(v)) == 1

	def get_path_switch_cost(self, path: List[int]):
		res = 0
		for u, v in zip(path[0:-1], path[1:]):
			res += self.g[u, v]["sc"]
		return res

	def get_path_delay(self, path: List[int]):
		res = 0
		for u, v in zip(path[0:-1], path[1:]):
			res += self.g[u, v]["delay"]
		return res

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
		self.K = 5
		self.nodes = list(range(self.network.g.number_of_nodes()))
		tmp = [(s, d) for s in self.nodes for d in self.nodes]
		self.src_dsts = list(filter(lambda x: x[0] != x[1], tmp))
		self.ksp = self.__cal_ksp()
		# 流量要求 （带宽、时延）
		self.demands: List[Tuple] = None
		self.lu_w = 0
		self.prob: cplex.Cplex = None
		self.ijk: List[List[List[List]]] = self.__cal_ijk()

	def __build_problem(self):
		prob = cplex.Cplex()
		prob.objective.set_sense(prob.objective.sense.minimize)
		demand_num = len(self.src_dsts)
		# 决策变量2*N(N-1)
		# 0代表第一类流，1代表第二类流
		var_names = ['x{}_{}_{}'.format(0, d, k) for d in range(demand_num) for k in range(self.K)]
		var_names.extend(
			['x{}_{}_{}'.format(1, d, k) for d in range(demand_num) for k in range(self.K)])

		# todo fix capacity vars
		prob.variables.add(names=var_names, types="I" * demand_num * self.K * 2)
		prob.variables.add(obj=[self.lu_w, 1], names=["u", "delay"])
		prob.parameters.simplex.limits.iterations.set(100000)
		prob.parameters.mip.tolerances.mipgap.set(0.0008)

		self.prob = prob

	def set_demand(self, demand: List[Tuple]):
		self.demands = demand

	def set_lu_weight(self, w: int):
		self.lu_w = w

	def __build_var_constraints(self):
		path_rows = []
		num_src_dsts = len(self.src_dsts)

		for i in range(num_src_dsts):
			large_volume_vars = ["x{}_{}_{}".format(0, i, k) for k in range(self.K)]
			path_rows.append([large_volume_vars, [1 for _ in range(self.K)]])
			low_latency_vars = ["x{}_{}_{}".format(1, i, k) for k in range(self.K)]
			path_rows.append([low_latency_vars, [1 for _ in range(self.K)]])

		names = []
		names.extend(['path{}_{}var_con'.format(0, d) for d in range(num_src_dsts)])
		names.extend(["path{}_{}var_con".format(1, d) for d in range(num_src_dsts)])
		self.prob.linear_constraints.add(lin_expr=path_rows,
		                                 senses="E" * num_src_dsts * 2,
		                                 rhs=[1 for _ in range(num_src_dsts * 2)],
		                                 names=names)

		# xik>=0
		# -xik<=0
		greater_than_zero = []
		for i in range(num_src_dsts):
			for k in range(self.K):
				greater_than_zero.append([["x{}_{}_{}".format(0, i, k)], [-1]])
				greater_than_zero.append([["x{}_{}_{}".format(1, i, k)], [-1]])
		constraint_names = []
		constraint_names.extend(
			["greater_than_zero_x{}_{}_{}con".format(0, i, k) for i in range(num_src_dsts) for k in
			 range(self.K)])
		constraint_names.extend(
			["greater_than_zero_x{}_{}_{}con".format(1, i, k) for i in range(num_src_dsts) for k in
			 range(self.K)])
		self.prob.linear_constraints.add(
			lin_expr=greater_than_zero,
			senses="L" * num_src_dsts * self.K * 2,
			rhs=[0 for _ in range(num_src_dsts * self.K * 2)],
			names=names
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
		info("build delay constraints")
		self.__build_delay_constraints()
		info("build constraints done")

	def __build_capacity_constraints(self):
		net = self.network
		num_src_dsts = len(self.src_dsts)
		# list[0]=volume
		large_volume_demands = self.demands[0:num_src_dsts]
		low_latency_demands = self.demands[num_src_dsts:]
		large_volumes = [d[0] for d in large_volume_demands]
		low_latency_volumes = [d[0] for d in low_latency_demands]

		capacities = []
		for u, v, d in net.g.edges(data=True):
			capacities.append(d['capacity'])
		# varss = ['x{}{}'.format(d, k) for d in range(demand_nums) for k in range(self.K)]
		var_names = ['x{}_{}_{}'.format(0, d, k) for d in range(num_src_dsts) for k in
		             range(self.K)]
		var_names.extend(
			['x{}_{}_{}'.format(1, d, k) for d in range(num_src_dsts) for k in range(self.K)])

		capacity_rows = []
		ijk = self.ijk

		for j in range(net.g.number_of_edges()):
			coeffs = []
			for i in range(num_src_dsts):
				demand = large_volumes[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][0])

			for i in range(num_src_dsts):
				demand = low_latency_volumes[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][1])

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
			for i in range(num_src_dsts):
				demand = large_volumes[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][0])

			for i in range(num_src_dsts):
				demand = low_latency_volumes[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][1])

			coeffs.append(-capacities[j])
			utility_rows.append([varss, coeffs])

		self.prob.linear_constraints.add(
			lin_expr=utility_rows,
			senses='L' * self.network.g.number_of_edges(),
			rhs=[0 for _ in range(self.network.g.number_of_edges())],
			names=['utilitycons{}'.format(j) for j in range(net.g.number_of_edges())]
		)

	def __build_delay_constraints(self):
		net = self.network
		num_src_dsts = len(self.src_dsts)

		link_delays = []
		for u, v, d in net.g.edges(data=True):
			link_delays.append(d['delay'])

		varss = ['x{}_{}_{}'.format(1, i, k) for i in range(num_src_dsts) for k in range(self.K)]
		varss.append("delay")
		coeffs = []
		for i, (src, dst) in enumerate(self.src_dsts):
			paths = self.ksp[(src, dst)][1]
			for k in range(self.K):
				coeffs.append(net.get_path_switch_cost(paths[k]) * net.get_path_delay(paths[k]))
		coeffs.append(-1)

		self.prob.linear_constraints.add(lin_expr=[[varss, coeffs]],
		                                 senses="L",
		                                 rhs=0,
		                                 names=["weighted_delay_constraint"]
		                                 )

	def __cal_ksp(self) -> Dict[Tuple, Tuple]:
		'''
		计算ksp
		:return:
		'''
		ksp_file = "ksp_{}.pkl".format(self.id)
		ksp_file = os.path.join(cache_dir, ksp_file)
		if pathlib.Path(ksp_file).is_file():
			debug("find cached ksp for {}".format(self.id))
			return load_pkl(ksp_file)
		debug("No cache found,calculating ksp")
		net = self.network
		res = {}
		for s, d in self.src_dsts:
			large_volume_paths = net.ksp(s, d, self.K)
			low_latence_paths = net.ksp(s, d, self.K, "delay")
			res[(s, d)] = (large_volume_paths, low_latence_paths)
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
		ijk = [[[[0, 0] for _ in range(self.K)] for _ in range(topo.number_of_edges())] for _ in
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
					if net.edge_in_path(u, v, p):
						ijk[i][j][k][1] = 1
		return ijk

	def solve(self):
		# res_file="labels/res_{}.pkl".format(self.id)
		# if pathlib.Path(res_file).is_file():
		# 	logger.debug("find cached result")
		# 	return load_pkl(res_file)
		assert self.demands is not None
		assert self.lu_w != 0
		self.__build_problem()
		self.__build_constraints()
		try:
			self.prob.solve()
		except cplex.exceptions.CplexSolverError as exc:
			err(exc)
			raise exc

		return self.prob.solution

	def solve_demo(self):
		res_file = "labels/res_{}.pkl".format(self.id)

		assert self.demands is not None
		assert self.lu_w != 0
		if self.prob is not None:
			del self.prob
		self.__build_problem()
		self.__build_constraints()
		self.prob.solve()
		self.prob.get_stats()
		obj = self.prob.solution.get_objective_value()
		print(obj)

		res = self.prob.solution.get_values()

		#utility,delay
		debug("link utility {},weighted delay {}".format(res[-2],res[-1]))

		# print(res[-2], res[-1])
		#action
		res = res[:-2]
		assert len(res) == 66 * 65 * self.K*2
		large_volume_res=res[0:66*65*self.K]
		low_latency_res=res[66*65*self.K:]

		max_idxs = []
		for i in range(0, len(large_volume_res), self.K):
			tmp = res[i:i + self.K]
			max_idxs.append(tmp.index(max(tmp)))

		counter = Counter(max_idxs)
		debug("Large volume res",counter)

		max_idxes=[]
		for i in range(0,len(low_latency_res),self.K):
			tmp=res[i:i+self.K]
			max_idxes.append(tmp.index(max(tmp)))
		counter=Counter(max_idxes)
		debug("Low latency res",counter)


if __name__ == '__main__':
	pass
