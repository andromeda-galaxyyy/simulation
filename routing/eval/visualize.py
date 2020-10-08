from routing.nn.minor_predictor import MultiProcessPredictor
from routing.instance import *
from typing import List, Tuple
from routing.ksp.ilp import ILPModel
from common.Graph import NetworkTopo
from routing.eval.evaluator import RoutingEvaluator
import matplotlib

matplotlib.use('agg')
import matplotlib.pyplot as plt
from routing.common import *
from path_utils import get_prj_root
from utils.file_utils import walk_dir
from utils.log_utils import debug
from utils.time_utils import now_in_milli
import random
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


def solve_and_visualize2(topo: List[List[Tuple]], instances: List[RoutingInput]):
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
	evaluator = RoutingEvaluator(topo, 3)
	ratio = []
	for instance in instances:
		ilp_utility = evaluator(instance)
		nn_inpt = RoutingInput(
			video=instance.video,
			iot=instance.iot,
			voip=instance.voip,
			ar=instance.ar
		)
		start = now_in_milli()
		nn_output = solver["nn"](nn_inpt)
		debug("nn solve done use {} milliseconds".format(now_in_milli() - start))
		# sleep(0.5)

		nn_instance = convert(nn_inpt, nn_output)
		nn_utility = evaluator(nn_instance)
		ratio.append((nn_utility - ilp_utility) / ilp_utility)
	return ratio


def plot(ratios: List[float]):
	plt.hist(ratios)
	plt.savefig("/tmp/demo.png")




if __name__ == '__main__':
	# load routing instances
	instances_fns = walk_dir(instances_dir, lambda s: "ilpinstance" in s)
	debug("find instances fns {}".format(len(instances_fns)))
	random.shuffle(instances_fns)
	instances_fns = instances_fns[:100]
	instances = []
	for fn in instances_fns:
		instances.extend(load_pkl(fn))

	topo = load_pkl(os.path.join(get_prj_root(), "cache", "topo.unlimited.pkl"))[0]

	ratios = solve_and_visualize2(topo, instances)
	plot(ratios)
