from routing.nn.minor_predictor import MultiProcessPredictor
from routing.instance import *
from typing import List, Tuple
from routing.ksp.ilp import ILPModel
from common.graph import NetworkTopo
from routing.eval.evaluator import RoutingEvaluator
from routing.eval.evaluator2 import RoutingEvaluator2
from routing.online.models import RoutingInput as OnlineInput
from routing.online.models import RoutingOutput as OnlineOutput
from routing.online.models import Routing as OnlineRouting

import matplotlib

from routing.online.online import Online
from utils.arch_utils import get_platform
if "darwin" in get_platform():
	matplotlib.use('TkAgg')
from scipy.stats import norm
import matplotlib.pyplot as plt
from routing.constant import *
from path_utils import get_prj_root
from utils.file_utils import walk_dir
from utils.log_utils import debug
from utils.time_utils import now_in_milli
import random
import numpy as np
from time import sleep

random.seed(now_in_milli())


def solve_and_visualize(topo: List[List[Tuple]], inpts: List[RoutingInput]):
	def convert(inp: RoutingInput, out: RoutingOutput) -> RoutingInstance:
		return RoutingInstance(
			video=inp.video,
			iot=inp.iot,
			voip=inp.voip,
			ar=inp.ar,
			labels={
				"video": out.video,
				"iot": out.iot,
				"voip": out.voip,
				"ar": out.ar
			}
		)

	solver = {
		"ilp": ILPModel(topo=NetworkTopo(topo), id=0),
		"nn": MultiProcessPredictor(66)
	}
	evaluator = RoutingEvaluator(topo, 3)
	ratio = []
	for inp in inpts:
		ilp_output = solver["ilp"](inp)
		ilp_instance = convert(inp, ilp_output)
		ilp_utility = evaluator(ilp_instance)
		nn_output = solver["nn"](inp)
		nn_instance = convert(inp, nn_output)
		nn_utility = evaluator(nn_instance)
		ratio.append((nn_utility - ilp_utility) / ilp_utility)


def solve_and_visualize2(topo: List[List[Tuple]], instances: List[RoutingInstance]):
	'''

	:param topo:
	:param inpts:
	:return:
	'''

	def convert(inp: RoutingInput, out: RoutingOutput) -> RoutingInstance:
		return RoutingInstance(
			video=inp.video,
			iot=inp.iot,
			voip=inp.voip,
			ar=inp.ar,
			labels={
				"video": out.video,
				"iot": out.iot,
				"voip": out.voip,
				"ar": out.ar
			}
		)

	solver = {
		"ilp": ILPModel(topo=NetworkTopo(topo), id=0),
		"nn": MultiProcessPredictor(66)
	}

	online = Online(NetworkTopo(topo))
	online.reset()
	evaluator = RoutingEvaluator(topo, 3)
	nn_ratios = []
	nn_utilities = []
	random_ratios = []
	random_utilities = []
	ospf_ratios = []
	ospf_utilities = []
	online_ratios = []
	online_utilities=[]

	online_evaluator = RoutingEvaluator2(topo, K=3)

	ilp_utilities = []
	for instance_idx,instance in enumerate(instances):
		ilp_utility = evaluator(instance)
		ilp_utilities.append(ilp_utility)
		inpt = RoutingInput(
			video=instance.video,
			iot=instance.iot,
			voip=instance.voip,
			ar=instance.ar
		)
		s = [0 for _ in range(66 * 65)]
		# ospf_output = RoutingOutput(video=s, iot=s, voip=s, ar=s)
		#
		# random_output = RoutingOutput(video=[np.random.randint(0, 3) for _ in range(66 * 65)],
		#                               iot=[np.random.randint(0, 3) for _ in range(66 * 65)]
		#                               , ar=[np.random.randint(0, 3) for _ in range(66 * 65)],
		#                               voip=[np.random.randint(0, 3) for _ in range(66 * 65)])

		start = now_in_milli()
		# nn_output = solver["nn"](inpt)
		# debug("nn solve done use {} milliseconds".format(now_in_milli() - start))
		#
		# nn_instance = convert(inpt, nn_output)
		# nn_utility = evaluator(nn_instance)
		# nn_utilities.append(nn_utility)
		# nn_ratios.append((nn_utility - ilp_utility) / ilp_utility)
		#
		# ospf_instance = convert(inpt, ospf_output)
		# ospf_utility = evaluator(ospf_instance)
		# ospf_utilities.append(ospf_utility)
		# ospf_ratios.append((ospf_utility - ilp_utility) / ilp_utility)
		#
		# random_utility = evaluator(convert(inpt, random_output))
		# random_utilities.append(random_utility)
		# random_ratios.append((random_utility - ilp_utility) / ilp_utility)

		online_traffic = [0 for _ in range(66 * 65)]
		for idx in range(66 * 65):
			online_traffic[idx] += inpt.video[idx]
			online_traffic[idx] += inpt.iot[idx]
			online_traffic[idx] += inpt.ar[idx]
			online_traffic[idx] += inpt.voip[idx]

		online_input = OnlineInput(traffic=online_traffic)
		online_output = online(online_input)
		online_routing = OnlineRouting(traffic=online_input.traffic, labels=online_output.labels)
		online_utility=online_evaluator(online_routing)
		online_utilities.append(online_utility)
		online_ratios.append((online_utility-ilp_utility)/ilp_utility)
		debug("online algorithm {} done".format(instance_idx))

	# save_pkl("/tmp/shortest.pkl", ospf_ratios)
	# save_pkl("/tmp/random.pkl", random_ratios)
	# save_pkl("/tmp/nn.pkl", nn_ratios)
	#
	# save_pkl("/tmp/random.utility.pkl", random_utilities)
	# save_pkl("/tmp/ospf.utility.pkl", ospf_utilities)
	# save_pkl("/tmp/ilp.utility.pkl", ilp_utilities)
	# save_pkl("/tmp/nn.utility.pkl", nn_utilities)
	save_pkl("/tmp/online.utility.pkl",online_utilities)
	save_pkl("/tmp/online.pkl",online_ratios)


# return nn_ratios


# def plot(ratios: List[float], style="-"):
# 	# x=np.linspace(0,2,100)
# 	y = norm.cdf(ratios)
# 	plt.plot(ratios, y)
# 	plt.show()


def plot_cdf():
	ma, mm = None, None
	random_ratios = load_pkl("/tmp/random.pkl")
	random_ratios = np.sort(random_ratios)
	ma = max(random_ratios)
	mm = min(random_ratios)
	y = np.arange(len(random_ratios)) / (len(random_ratios) - 1)
	random_plot, = plt.plot(random_ratios, y, label="随机")

	ospf_ratios = load_pkl("/tmp/shortest.pkl")
	ospf_ratios = np.sort(ospf_ratios)
	ma = max(ma, max(ospf_ratios))
	mm = min(mm, min(ospf_ratios))

	y = np.arange(len(ospf_ratios)) / (len(ospf_ratios) - 1)
	ospf, = plt.plot(ospf_ratios, y, label="最短路")
	nn_ratios = load_pkl("/tmp/nn.pkl")
	nn_ratios = np.sort(nn_ratios)
	ma = max(ma, max(nn_ratios))
	mm = min(mm, min(nn_ratios))
	y = np.arange(len(nn_ratios)) / (len(nn_ratios) - 1)

	nn, = plt.plot(nn_ratios, y, label="监督学习")
	plt.xlabel("g(u)")
	plt.ylabel("累计分布")
	plt.title("三种路由方案g(u)累计分布")
	plt.legend(handles=[random_plot, ospf, nn])

	plt.savefig("/tmp/fig.png", dpi=300)
	plt.show()


if __name__ == '__main__':
	# test()
	# load routing instances
	inst_dir = os.path.join(get_prj_root(), "routing", "instances.5.3")
	instances_fns = walk_dir(inst_dir, lambda s: "ilpinstance" in s)
	debug("find instances fns {}".format(len(instances_fns)))
	# random.shuffle(instances_fns)
	# num=int(len(instances_fns)*0.8)
	instances_fns = instances_fns[-8:]
	instances = []
	for fn in instances_fns:
		instances.extend(load_pkl(fn))

	topo = load_pkl(os.path.join(get_prj_root(), "cache", "topo.unlimited.pkl"))[0]

	ratios = solve_and_visualize2(topo, instances)
# plot(ratios)
