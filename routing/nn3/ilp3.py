import numpy as np
from utils.common_utils import load_pkl
from typing import List, Tuple, Dict
import cplex
from utils.common_utils import info, err
import os
from path_utils import get_prj_root
from routing.nn3.models import RoutingInput, RoutingOutput, Routing
from common.graph import NetworkTopo
from routing.eval.evaluator3 import RoutingEvaluator3
from utils.file_utils import load_json
from utils.log_utils import debug, info, err
from utils.time_utils import now_in_milli

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


class ILPModel:
	def __init__(self, topo: NetworkTopo, id_=0):
		self.network = topo
		self.id = id_
		self.K = 5
		self.nodes = list(range(self.network.g.number_of_nodes()))
		tmp = [(s, d) for s in self.nodes for d in self.nodes]
		self.src_dsts = list(filter(lambda x: x[0] != x[1], tmp))
		self.ksp = self.__cal_ksp()
		# 流量要求 （带宽、时延）
		self.demands: List[Tuple] = None
		self.input: RoutingInput = None
		self.prob: cplex.Cplex = None
		self.ijk: List[List[List[List]]] = self.__cal_ijk()

	def __build_problem(self):
		info("build problem")
		prob = cplex.Cplex()
		prob.objective.set_sense(prob.objective.sense.minimize)
		demand_num = len(self.src_dsts)

		var_names = []
		for flow_idx in range(1):
			var_names.extend(
				['x{}_{}_{}'.format(flow_idx, d, k) for d in range(demand_num) for k in
				 range(self.K)])

		prob.variables.add(names=var_names, types="I" * demand_num * self.K * 1)
		prob.variables.add(obj=[1], names=["u"])
		prob.parameters.simplex.limits.iterations.set(100000)
		prob.parameters.mip.tolerances.mipgap.set(0.0008)

		self.prob = prob

	def __build_var_constraints(self):
		path_rows = []
		num_src_dsts = len(self.src_dsts)

		for flow_idx in range(1):
			for i in range(num_src_dsts):
				volume_vars = ["x{}_{}_{}".format(flow_idx, i, k) for k in range(self.K)]
				path_rows.append([volume_vars, [1 for _ in range(self.K)]])

		names = []
		for flow_idx in range(1):
			names.extend(['path{}_{}var_con'.format(flow_idx, d) for d in range(num_src_dsts)])

		self.prob.linear_constraints.add(lin_expr=path_rows,
		                                 senses="E" * num_src_dsts * 1,
		                                 rhs=[1 for _ in range(num_src_dsts * 1)],
		                                 names=names)

		# xik>=0
		# -xik<=0
		greater_than_zero = []
		constraint_names = []
		for i in range(num_src_dsts):
			for k in range(self.K):
				for flow_idx in range(1):
					greater_than_zero.append([["x{}_{}_{}".format(flow_idx, i, k)], [-1]])
					constraint_names.append("greater_than_zero_x{}_{}_{}con".format(flow_idx, i, k))

		self.prob.linear_constraints.add(
			lin_expr=greater_than_zero,
			senses="L" * num_src_dsts * self.K * 1,
			rhs=[0 for _ in range(num_src_dsts * self.K * 1)],
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
		ilp_input: RoutingInput = self.input
		# list[0]=volume
		demands = ilp_input.traffic
		# iot_demands = ilp_input.iot
		# voip_demands = ilp_input.voip
		# ar_demands = ilp_input.ar

		capacities = []
		for u, v, d in net.g.edges(data=True):
			capacities.append(d['capacity'])
		var_names = []
		for flow_idx in range(1):
			for d in range(num_src_dsts):
				for k in range(self.K):
					var_names.append('x{}_{}_{}'.format(flow_idx, d, k))

		capacity_rows = []
		ijk = self.ijk

		for j in range(net.g.number_of_edges()):
			coeffs = []
			for i in range(num_src_dsts):
				demand = demands[i]
				for k in range(self.K):
					coeffs.append(demand * ijk[i][j][k][0])

			# for i in range(num_src_dsts):
			# 	demand = iot_demands[i]
			# 	for k in range(self.K):
			# 		coeffs.append(demand * ijk[i][j][k][1])
			#
			# for i in range(num_src_dsts):
			# 	demand = voip_demands[i]
			# 	for k in range(self.K):
			# 		coeffs.append(demand * ijk[i][j][k][2])
			# for i in range(num_src_dsts):
			# 	demand = ar_demands[i]
			# 	for k in range(self.K):
			# 		coeffs.append(demand * ijk[i][j][k][3])

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
			for flow_idx, demandss in enumerate(
					[demands]):
				for i in range(num_src_dsts):
					demand = demandss[i]
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

	def __cal_ksp(self) -> Dict[Tuple,List]:
		return ksps

	def __cal_ijk(self) -> List[List[List[List]]]:
		"""
		determined for flow i ,whether edge j is in kth path
		:return:
		三维数组，每个元素为一个list，第一个表示大带宽流，第二个表示低延迟流
		"""
		net = self.network
		topo = net.g
		ijk = [[[[0] for _ in range(self.K)] for _ in range(topo.number_of_edges())] for _
		       in range(len(self.src_dsts))]

		for i, (src, dst) in enumerate(self.src_dsts):
			paths= self.ksp[(src, dst)]
			edges = list(topo.edges(data=True))
			for j in range(topo.number_of_edges()):
				u, v, _ = edges[j]
				for k in range(self.K):
					p = paths[k]
					if net.edge_in_path(u, v, p):
						ijk[i][j][k][0] = 1
		return ijk

	def __call__(self, ilp_input: RoutingInput) -> RoutingOutput:
		self.input = ilp_input
		self.__build_problem()
		self.__build_constraints()
		try:
			self.prob.solve()
			actions = self.prob.solution.get_values()[:-1]
			# print(self.prob.solution.get_values()[-1])
			assert len(actions) == len(self.src_dsts) * self.K * 1
			n_demand = len(self.src_dsts)
			# video,iot,voip,ar

			video_res = None
			# iot_res = None
			# voip_res = None
			# ar_res = None
			for flow_idx in range(1):
				action = actions[flow_idx * n_demand * self.K:(flow_idx + 1) * n_demand * self.K]
				values = []
				for demand_idx in range(n_demand):
					tmp = action[demand_idx * self.K:(demand_idx + 1) * self.K]

					values.append(tmp.index(max(tmp)))
					# if flow_idx == 0:
						# video_res = values
					# elif flow_idx == 1:
					# 	iot_res = values
					# elif flow_idx == 2:
					# 	voip_res = values
					# else:
					# 	ar_res = values

			return RoutingOutput(labels=values)
		except cplex.exceptions.CplexSolverError as exc:
			err(exc)
			return None


def test_ilp():
	# np.random.seed(seed=now_in_milli())
	np.random.seed()

	topos_fn = os.path.join(static_dir, "military.pkl")
	topo = load_pkl(topos_fn)[0]["topo"]
	# debug(topo)
	ilp_input = RoutingInput(traffic=[np.random.rand() for _ in range(100*99)])


	while True:
		network = NetworkTopo(topo)
		ilp_model = ILPModel(network)
		ilp_output = ilp_model(ilp_input)
		if ilp_output is None:
			debug("enlarge link capacity by 10x")
			#enlarge topo
			for i in range(100):
				for j in range(100):
					if -1 in topo[i][j]:continue
					a,b,c,d=topo[i][j]
					a=a*10
					topo[i][j]=(a,b,c,d)
			continue
		else:
			break

	utility = ilp_model.prob.solution.get_values()[-1]
	# debug(ilp_output.labels)
	debug(utility)
	evaluator = RoutingEvaluator3(topo, 5)
	debug(evaluator(routing=Routing(traffic=ilp_input.traffic,labels=ilp_output.labels)))


if __name__ == '__main__':
	test_ilp()
