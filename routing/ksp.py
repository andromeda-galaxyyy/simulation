import matplotlib

matplotlib.use('agg')
import numpy as np
from utils.common_utils import load_pkl, save_pkl, save_json, is_digit, check_file, check_dir, \
	file_exsit, dir_exsit
import matplotlib.pyplot as plt
import networkx as nx
from itertools import islice
import pathlib
import random
from collections import Counter
from typing import List, Tuple, Dict, DefaultDict
import cplex
from utils.common_utils import debug, info, err
from utils.num_utils import gaussion, uniform
import os
from path_utils import get_prj_root
from copy import deepcopy
from argparse import ArgumentParser
import tmgen
from tmgen.models import random_gravity_tm

cache_dir = os.path.join(get_prj_root(), "cache")
satellite_topo_dir = os.path.join(get_prj_root(), "routing/satellite_topos")
static_dir=os.path.join(get_prj_root(),"static")

def is_connected(topo, i, j):
	if not is_digit(topo[i][j]):
		return False
	return float(topo[i][j]) > 0


def link_switch_cost(inter: float):
	return 10 / np.exp(inter / 100)


def read_statellite_topo():
	satellite_topos=[]
	fn = os.path.join(satellite_topo_dir, "delaygraph_py3_v2.txt")
	old_topos = load_pkl(fn)
	intervals = []
	for _ in range(22):
		intervals.append(157)
		intervals.append(116)
	epoch_time = sum(intervals)
	long_lasting_edge = set()
	exits_intervals = []
	new_topos = []

	for old_topo_idx, old_topo in enumerate(old_topos):
		links = set()
		nodes = len(old_topo)
		new_topo = [[[-1,-1,-1,-1] for _ in range(nodes)] for _ in range(nodes)]

		for i in range(nodes):
			for j in range(i + 1, nodes):
				if not is_connected(old_topo, i, j):
					continue
				links.add((i, j))
				# capacity = uniform(4000, 7000)
				capacity=100
				delay = float(old_topo[i][j])
				delay*=1000
				delay=int(delay)

				# 容量，延迟、loss,switch_cost
				spec = [capacity, delay, 0,0]
				next_iterval = 0
				idx2 = old_topo_idx
				always_connected = False
				count_interval = 0
				while True:
					count_interval += 1
					next_iterval += intervals[idx2]
					idx2 = (idx2 + 1) % len(old_topos)
					next_old_topo = old_topos[idx2]

					if not is_connected(next_old_topo, i, j):
						exits_intervals.append(count_interval)
						break
					if next_iterval > epoch_time:
						long_lasting_edge.add((i, j))
						always_connected = True
						break
				if always_connected:
					spec[-1] = 0
				else:
					spec[-1] = float(link_switch_cost(next_iterval))
				# print(spec[2])
				new_topo[i][j] = deepcopy(spec)
				new_topo[j][i] = deepcopy(spec)
		# print(len(links))
		new_topos.append(deepcopy(new_topo))
		satellite_topos.append({
			"topo":new_topo,
			"duration":intervals[old_topo_idx]
		})
	assert len(satellite_topos)==44

	topo_fn = os.path.join(cache_dir, "topo.pkl")

	save_pkl(topo_fn, new_topos)
	save_pkl(os.path.join(static_dir,"satellite_overall.pkl"),satellite_topos)
	debug("satellite topo saved")


class NetworkTopo:
	def __init__(self, topo: List[List[List]]):
		self.g = self.__gen_graph(topo)
		self.weights = []

	# self.plot()

	def __gen_graph(self, topo: List[List[List]]):
		g = nx.Graph()
		num_nodes = len(topo)
		g.add_nodes_from(list(range(num_nodes)))
		for i in range(num_nodes):
			for j in range(i + 1, num_nodes):
				if -1 in topo[i][j]:continue
				capacity, delay, loss,sc = topo[i][j]
				assert capacity >= 0
				g.add_edge(i, j, weight=4000 / capacity, capacity=capacity, delay=delay, sc=sc,loss=loss)

		return g

	@staticmethod
	def edge_in_path(u, v, path: List[int]):
		if u not in path: return False
		if v not in path: return False
		return abs(path.index(u) - path.index(v)) == 1

	def get_path_switch_cost(self, path: List[int]):
		res = 0
		for u, v in zip(path[0:-1], path[1:]):
			res += self.g.edges[u, v]["sc"]
		return res

	def get_path_delay(self, path: List[int]):
		res = 0
		for u, v in zip(path[0:-1], path[1:]):
			res += self.g.edges[u, v]["delay"]
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
		                                 rhs=[0],
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

		# utility,delay
		debug("link utility {},weighted delay {}".format(res[-2], res[-1]))

		# print(res[-2], res[-1])
		# action
		res = res[:-2]
		assert len(res) == 66 * 65 * self.K * 2
		large_volume_res = res[0:66 * 65 * self.K]
		low_latency_res = res[66 * 65 * self.K:]

		max_idxs = []
		for i in range(0, len(large_volume_res), self.K):
			tmp = large_volume_res[i:i + self.K]
			max_idxs.append(tmp.index(max(tmp)))

		counter = Counter(max_idxs)
		debug("Large volume res {}".format(counter))

		max_idxes = []
		for i in range(0, len(low_latency_res), self.K):
			tmp = low_latency_res[i:i + self.K]
			max_idxes.append(tmp.index(max(tmp)))
		counter = Counter(max_idxes)
		debug("Low latency res:{}".format(counter))


def demo_ilp():
	topos_fn = os.path.join(cache_dir, "topo.pkl")
	topo = load_pkl(topos_fn)[0]
	n_nodes = len(topo)
	demands = []
	large_volume_tms = random_gravity_tm(n_nodes, 66 * 65 * 10).at_time(0).tolist()
	low_latency_tms = random_gravity_tm(n_nodes, 66 * 65 * 2).at_time(0).tolist()
	for src in range(n_nodes):
		for dst in range(n_nodes):
			if src == dst: continue
			demands.append((large_volume_tms[src][dst], 0))
	for src in range(n_nodes):
		for dst in range(n_nodes):
			if src == dst: continue
			demands.append((low_latency_tms[src][dst], 0))

	net = NetworkTopo(topo)
	model = ILPModel(net)
	model.set_lu_weight(5)
	model.set_demand(demands)
	model.solve_demo()


def generate_raw_labels():
	'''
	save raw labels, only save max idx
	:return:
	'''
	limit = 2000
	'''
	生成训练数据（未处理）
	:return: void
	'''
	raw_labels_dir = os.path.join(get_prj_root(), "routing/raw_labels")
	topo_file = os.path.join(get_prj_root(), "cache/topo.pkl")
	if not file_exsit(topo_file):
		err("Cannot find satellite topo file")
		exit(-1)
	topos = load_pkl(topo_file)
	n_nodes = len(topos[0])
	for idx, topo in enumerate(topos):
		dir_n = os.path.join(raw_labels_dir, str(idx))
		if not dir_exsit(dir_n):
			os.mkdir(dir_n)
		mask = [0 for _ in range(limit)]
		for f in os.listdir(dir_n):
			if ".pkl" not in f: continue
			mask[int(f[:-4])] = 1
		network = NetworkTopo(topo)
		model = ILPModel(network, idx)
		model.set_lu_weight(15)
		tms = []
		for i in range(limit):
			if mask[i] == 1: continue
			fn = os.path.join(dir_n, "{}.pkl".format(i))
			large_volume_all = n_nodes * (n_nodes - 1) * 5
			low_latency_all = n_nodes * (n_nodes - 1) * 1

			large_volume_tm = random_gravity_tm(n_nodes, large_volume_all).at_time(0).tolist()
			low_latency_tm = random_gravity_tm(n_nodes, low_latency_all).at_time(0).tolist()
			for src in range(n_nodes):
				for dst in range(n_nodes):
					if src == dst: continue
					tms.append((large_volume_tm[src][dst], 0))

			for src in range(n_nodes):
				for dst in range(n_nodes):
					if src == dst: continue
					tms.append((low_latency_tm[src][dst], 0))
			model.set_demand(tms)
			debug("Start to solve ilp model")
			try:
				n_src_dst = n_nodes * (n_nodes - 1)
				solution = model.solve()
				obj = solution.get_objective_value()
				res = solution.get_values()
				print(res[-2], res[-1], obj)
				action = res[:-2]

				large_volume_actions = action[0:n_src_dst]
				low_latency_actions = action[n_src_dst:]
				max_idxs1 = []
				for k in range(0, len(large_volume_actions), 5):
					tmp = large_volume_actions[k:k + 5]
					max_idxs1.append(tmp.index(max(tmp)))

				counter = Counter(max_idxs1)
				info("Large volume actions stats:\n {}".format(counter))

				max_idxs2 = []
				for k in range(0, len(low_latency_actions), 5):
					tmp = low_latency_actions[k:k + 5]
					max_idxs2.append(tmp.index(max(tmp)))

				counter = Counter(max_idxs2)

				info("Low latency actions stats:\n {}".format(counter))
				res_ = []
				res_.extend(max_idxs1)
				res_.extend(max_idxs2)
				res_.append(res[-2])
				res_.append(res[-1])
				save_pkl(fn, (tms,res_,obj))

			except cplex.exceptions.CplexSolverError as exc:
				err(exc)


if __name__ == '__main__':
	print("running mode:\n"
	      "1 read and save topo\n"
	      "2 generate raw labels\n"
	      "3 run demo ilp model")
	parser = ArgumentParser()
	parser.add_argument("--mode", type=int, default=1, help="running mode")
	args = parser.parse_args()
	mode = int(args.mode)
	if mode == 1:
		read_statellite_topo()
	elif mode == 2:
		generate_raw_labels()
	elif mode == 3:
		demo_ilp()
	else:
		err("Invalid argument")
		exit(-1)
