from routing.ksp.ilp2 import ILPModel
from routing.instance import ILPInstance
from routing.instance import ILPInput
from routing.instance import ILPOutput
from typing import List, Tuple, Callable
from utils.log_utils import debug, info, err
from routing.ksp.ilp2 import NetworkTopo
from utils.time_utils import now_in_seconds
from utils.file_utils import *
from path_utils import get_prj_root
from multiprocessing import Process
import random

cache_dir = os.path.join(get_prj_root(), "cache")
satellite_topo_dir = os.path.join(get_prj_root(), "routing/satellite_topos")
static_dir = os.path.join(get_prj_root(), "static")


def ilpinput_loader(fn: str) -> List[ILPInput]:
	'''
	read file specified by fn,generate ilpinput
	:param fn:
	:return:
	'''
	return load_pkl(fn)


def topo_loader(fn: str) -> List[List[Tuple]]:
	'''
	load topo from file
	:param fn:
	:return:
	'''
	return load_pkl(fn)[0]


def generate_labels(worker_id: int, traffic_fn: str, topo_fn: str,
                    traffic_loader_func: Callable[[str], List[ILPInput]],
                    topo_loader_func: Callable[[str], List[List[Tuple]]]):
	'''
	:param topo_loader_func:
	:param traffic_fn:
	:param traffic_loader_func:
	:param output:
	:return:
	'''
	partition_idx = 0
	partition_size = 1024
	inputs: List[ILPInput] = traffic_loader_func(traffic_fn)
	info("Loads {} ksp inputs".format(len(inputs)))

	topo = topo_loader_func(topo_fn)
	model = ILPModel(NetworkTopo(topo), 0)
	output: List[ILPInstance] = []
	for idx, inp in enumerate(inputs):
		start = now_in_seconds()
		out = model.solve(inp)
		end = now_in_seconds()
		if out is None: continue
		info("Solve {}th problem use seconds {}".format(idx, end - start))
		instance = ILPInstance(video=inp.video, iot=inp.iot, voip=inp.voip, ar=inp.ar, labels={
			"video": out.video,
			"iot": out.iot,
			"ar": out.iot,
			"voip": out.voip
		})
		output.append(instance)
		if len(output) >= partition_size:
			fn = os.path.join(cache_dir, "traffic/ilpoutput.{}.partition.{}.pkl".format(worker_id,
			                                                                            partition_idx))
			save_pkl(fn, output)
			debug("save to file {}".format(fn))
			partition_idx += 1
			output = []

		save_pkl(os.path.join(cache_dir, "traffic/ilpoutput.{}.partition.{}.pkl".format(worker_id,
		                                                                                partition_idx)),
		         output)

		fn = os.path.join(cache_dir,
		                  "traffic/ilpoutput.{}.partition.{}.pkl".format(worker_id, partition_idx))
		debug("save to file {}".format(fn))


def generate_labels_worker(worker_id: int, inputs: List[ILPInput], topo: List[List[Tuple]]):
	'''
	:param worker_id:
	:param inputs:
	:param topo
	:return:
	'''
	partition_idx = 0
	partition_size = 512

	info("Loads {} ksp inputs".format(len(inputs)))
	model = ILPModel(NetworkTopo(topo), 0)
	output: List[ILPInstance] = []
	for idx, inp in enumerate(inputs):
		start = now_in_seconds()
		out = model.solve(inp)
		end = now_in_seconds()
		if out is None: continue
		info("Solve {}th problem use seconds {}".format(idx, end - start))
		instance = ILPInstance(video=inp.video, iot=inp.iot, voip=inp.voip, ar=inp.ar, labels={
			"video": out.video,
			"iot": out.iot,
			"ar": out.iot,
			"voip": out.voip
		})
		output.append(instance)
		if len(output) >= partition_size:
			fn = os.path.join(cache_dir, "traffic/ilpoutput.{}.partition.{}.pkl".format(worker_id,
			                                                                            partition_idx))
			save_pkl(fn, output)
			debug("save to file {}".format(fn))
			partition_idx += 1
			output = []
		if idx == len(inputs) - 1:
			save_pkl(
				os.path.join(cache_dir, "traffic/ilpoutput.{}.partition.{}.pkl".format(worker_id,
				                                                                       partition_idx)),
				output)

			fn = os.path.join(cache_dir,
			                  "traffic/ilpoutput.{}.partition.{}.pkl".format(worker_id,
			                                                                 partition_idx))
			debug("save to file {}".format(fn))


if __name__ == '__main__':
	traffic_fn = os.path.join(cache_dir, "traffic/ilp_inputs.pkl")
	topo_fn = os.path.join(cache_dir, "topo.unlimited.pkl")
	topo = topo_loader(topo_fn)
	n_workers = 5
	processes = []
	ilpinputs = ilpinput_loader(traffic_fn)
	for _ in range(5):
		random.shuffle(ilpinputs)

	info("loaded {} ilpinputs".format(len(ilpinputs)))
	n_inputs_per_worker = len(ilpinputs) // n_workers
	for wid in range(n_workers):
		inps = ilpinputs[wid * n_inputs_per_worker:(wid + 1) * n_inputs_per_worker]
		processes.append(Process(target=generate_labels_worker, args=(wid, inps, topo)))

	for p in processes:
		p.start()
	for p in processes:
		p.join()
