from routing.ksp.ilp import ILPModel
from routing.instance import RoutingInstance
from routing.instance import RoutingInput
from routing.instance import RoutingOutput, log_ilpoutput
from typing import List, Tuple, Callable
from utils.log_utils import debug, info, err
from routing.ksp.ilp import NetworkTopo
from utils.time_utils import now_in_seconds
from utils.file_utils import *
from path_utils import get_prj_root
from multiprocessing import Process
import random
from argparse import ArgumentParser

cache_dir = os.path.join(get_prj_root(), "cache")
satellite_topo_dir = os.path.join(get_prj_root(), "routing/satellite_topos")
static_dir = os.path.join(get_prj_root(), "static")


def ilpinput_loader(fn: str) -> List[RoutingInput]:
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
                    traffic_loader_func: Callable[[str], List[RoutingInput]],
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
	inputs: List[RoutingInput] = traffic_loader_func(traffic_fn)
	info("Loads {} ksp inputs".format(len(inputs)))

	topo = topo_loader_func(topo_fn)
	model = ILPModel(NetworkTopo(topo), 0)
	output: List[RoutingInstance] = []
	for idx, inp in enumerate(inputs):
		start = now_in_seconds()
		out = model.__call__(inp)
		log_ilpoutput(out)
		end = now_in_seconds()
		if out is None: continue
		info("Solve {}th problem use seconds {}".format(idx, end - start))
		instance = RoutingInstance(video=inp.video, iot=inp.iot, voip=inp.voip, ar=inp.ar, labels={
			"video": out.video,
			"iot": out.iot,
			"ar": out.iot,
			"voip": out.voip
		})
		output.append(instance)
		if len(output) >= partition_size:
			fn = os.path.join(cache_dir, "traffic/ilpinstance.{}.partition.{}.pkl".format(worker_id,
			                                                                              partition_idx))
			save_pkl(fn, output)
			debug("save to file {}".format(fn))
			partition_idx += 1
			output = []

		save_pkl(os.path.join(cache_dir, "traffic/ilpinstance.{}.partition.{}.pkl".format(worker_id,
		                                                                                  partition_idx)),
		         output)

		fn = os.path.join(cache_dir,
		                  "traffic/ilpoutput.{}.partition.{}.pkl".format(worker_id, partition_idx))
		debug("save to file {}".format(fn))


def get_process(worker_id: int):
	fn = os.path.join(cache_dir, "traffic","ilpinstance","{}.process".format(worker_id))
	if not file_exsit(fn):
		return -1
	with open(fn, "r") as fp:
		return int(fp.readline())


def save_process(worker_id: int, p: int):
	fn = os.path.join(cache_dir, "traffic","ilpinstance","{}.process".format(worker_id))
	with open(fn, "w") as fp:
		fp.write("{}\n".format(p))


def generate_labels_worker(worker_id: int, inputs: List[RoutingInput], topo: List[List[Tuple]]):
	'''
	:param worker_id:
	:param inputs:
	:param topo
	:return:
	'''
	partition_size = 128

	last_p = get_process(worker_id)
	info("Last process {}".format(last_p))
	info("Loads {} ksp inputs".format(len(inputs)))

	n_partitions = len(inputs) // partition_size
	debug("partitions {}".format(n_partitions))
	inputs = inputs[:n_partitions * partition_size]

	model = ILPModel(NetworkTopo(topo), 0)

	for partition_idx in range(n_partitions):
		if partition_idx <= last_p: continue
		partition_inputs = inputs[
		                   partition_idx * partition_size:(partition_idx + 1) * partition_size]

		output: List[RoutingInstance] = []
		for idx, inp in enumerate(partition_inputs):
			start = now_in_seconds()
			out = model.__call__(inp)
			end = now_in_seconds()
			if out is None: continue
			log_ilpoutput(out)
			info("Solve {}th problem use seconds {}".format(idx + partition_idx * partition_size,
			                                                end - start))
			instance = RoutingInstance(video=inp.video, iot=inp.iot, voip=inp.voip, ar=inp.ar,
			                           labels={
				                           "video": out.video,
				                           "iot": out.iot,
				                           "voip": out.voip,
				                           "ar": out.ar,
			                           })
			output.append(instance)

		fn = os.path.join(cache_dir, "traffic", "ilpinstance",
		                  "ilpinstance.{}.partition.{}.pkl".format(worker_id,
		                                                           partition_idx))
		save_pkl(fn, output)
		debug("save to file {}".format(fn))
		save_process(worker_id, partition_idx)


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("--workers", type=int, help="number of workers", default=2)
	parser.add_argument("--id", type=int, help="id", default=0)
	args = parser.parse_args()
	traffic_fn = os.path.join(cache_dir, "traffic/ilp_inputs4.pkl")
	topo_fn = os.path.join(cache_dir, "topo.unlimited.pkl")
	topo = topo_loader(topo_fn)
	n_process = 10
	processes = []
	ilpinputs = ilpinput_loader(traffic_fn)
	id_ = int(args.id)
	n_worker = int(args.workers)
	task_per_worker = len(ilpinputs) // n_worker
	ilpinputs = ilpinputs[id_ * task_per_worker:(id_ + 1) * task_per_worker]

	info("loaded {} ilpinputs".format(len(ilpinputs)))
	n_inputs_per_worker = len(ilpinputs) // n_process
	for wid in range(n_process):
		inps = ilpinputs[wid * n_inputs_per_worker:(wid + 1) * n_inputs_per_worker]
		processes.append(Process(target=generate_labels_worker, args=(wid, inps, topo)))

	for p in processes:
		p.start()
	for p in processes:
		p.join()
