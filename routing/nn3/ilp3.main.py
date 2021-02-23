from argparse import ArgumentParser
from typing import List, Tuple
from utils.log_utils import debug, info, err
import os
import numpy as np
from path_utils import get_prj_root
from utils.file_utils import file_exsit, read_lines, load_json, load_pkl, save_json, save_pkl, \
	read_lines_with_action
from utils.file_utils import write_to_file
from routing.nn3.ilp3 import ILPModel
from common.graph import NetworkTopo
import json
import time
from utils.time_utils import now_in_milli, now_in_seconds
from multiprocessing import Process
import signal

from routing.nn3.models import *

n = 10


def run_in_worker(worker_id: int, inputs: List[RoutingInput]):
	debug("this is worker {}".format(worker_id))
	process_dir = os.path.join(get_prj_root(), "routing/nn3/.process")
	topo_fn = os.path.join(get_prj_root(), "static/topo.json")
	topo = load_json(topo_fn)["topo"]
	# enlarge topo
	for i in range(100):
		for j in range(100):
			if -1 in topo[i][j]: continue
			a, b, c, d = topo[i][j]
			a *= 10
			topo[i][j] = (a, b, c, d)
	labels_dirs = os.path.join(get_prj_root(), "routing/nn3/labels")

	process_fn = os.path.join(process_dir, "{}.ilp.process".format(worker_id))

	curr_process = 0
	if file_exsit(process_fn):
		lines = read_lines(process_fn)
		if len(lines) != 0:
			curr_process = int(lines[0])
	curr_process -= n
	if curr_process < 0:
		curr_process = 0

	routings: List[Routing] = []

	# # set up sigterm
	# def sig_term_handler(sig, frame):
	# 	debug("worker {} recevied signal {} now exit".format(worker_id, sig))
	# 	partition_fnn = os.path.join(labels_dirs,
	# 	                             "{}.{}.partition".format(worker_id, now_in_seconds()))
	# 	save_pkl(partition_fnn, routings)
	#
	# signal.signal(signal.SIGINT, sig_term_handler)
	# signal.signal(signal.SIGTERM, sig_term_handler)
	# signal.signal(signal.SIGKILL, sig_term_handler)

	for rinput_idx in range(curr_process, len(inputs)):
		debug("solving {}th problems".format(rinput_idx))
		rinput = inputs[rinput_idx]
		debug("max traffic {}".format(max(rinput.traffic)))
		while True:
			network = NetworkTopo(topo)
			ilp_model = ILPModel(network, id_=worker_id)
			routing_output = ilp_model(rinput)
			if routing_output is None:
				debug("enlarge link capacity by 10x")
				# enlarge topo
				for i in range(100):
					for j in range(100):
						if -1 in topo[i][j]: continue
						a, b, c, d = topo[i][j]
						a = a * 10
						topo[i][j] = (a, b, c, d)
				continue
			else:
				break
		routings.append(Routing(traffic=rinput.traffic, labels=routing_output.labels))
		curr_process += 1
		write_to_file(curr_process, process_fn)
		if len(routings) == n or rinput_idx == len(inputs) - 1:
			partition_fn = os.path.join(labels_dirs,
			                            "{}.{}.partition".format(worker_id, now_in_seconds()))
			save_pkl(partition_fn, routings)
			routings = []


# write to file


def load_raw_traffic_matrix(dir_name: str) -> List[List[float]]:
	res: List[List[float]] = []

	def action(line: str):
		obj = json.loads(line)
		if max(obj["0"]) > 2:
			if len(obj["0"])!=100*99:
				return None
			return obj["0"]
		return None

	fns=[]
	for file in os.listdir(dir_name):
		if "matrix" not in file: continue
		fns.append(file)
	fns.sort()
	for fn in fns:
		debug("loading file {}".format(fn))
		fn = os.path.join(dir_name, fn)
		tmp = read_lines_with_action(fn, action)
		res.extend(tmp)

	# res = read_lines_with_action(os.path.join(dir_name, "matrixLarge.txt"), action)
	#filter
	res=[r for r in res if r is not None]
	return res


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("--machines", type=int, help="number of workers", default=7)
	parser.add_argument("--id_", type=int, default=0)
	parser.add_argument("--process", type=int, default=10)
	parser.add_argument("--dir", type=str, default="/tmp/data01211655")

	args = parser.parse_args()

	debug("loading traffic matrix")
	traffic_matrixs = load_raw_traffic_matrix(args.dir)
	debug("traffic matrix loaded done")
	debug("all problems {}".format(len(traffic_matrixs)))
	n_process = int(args.process)
	n_machines = int(args.machines)
	self_id = int(args.id_)
	debug("{} process per machine,{} machines, id {}".format(n_process, n_machines, self_id))
	problems_per_machine = len(traffic_matrixs) // n_machines
	self_problems = traffic_matrixs[
	                self_id * problems_per_machine:(self_id + 1) * problems_per_machine]

	ilp_inputs = [RoutingInput(traffic=p) for p in self_problems]

	processes: List[Process] = []

	n_problem_perprocess = int(np.ceil(len(self_problems) / n_process))
	for idx in range(n_process):
		start = idx * n_problem_perprocess
		end = (idx + 1) * n_problem_perprocess
		if end > len(ilp_inputs):
			end = len(ilp_inputs)
		debug("process {},start {},end {}".format(idx, start, end))

		ilp_inputs_per_process = ilp_inputs[start:end]

		global_worker_id = self_id * n_process + idx
		debug("start worker with id {}".format(global_worker_id))
		processes.append(
			Process(target=run_in_worker, args=(global_worker_id, ilp_inputs_per_process)))

	for p in processes:
		p.start()


	def handle_signal(sig, frame):
		debug("received signal {},terminate child process".format(sig))
		for p in processes:
			p.terminate()


	# debug("set up signal")
	# signal.signal(signal.SIGINT, handle_signal)
	# signal.signal(signal.SIGTERM, handle_signal)
	# signal.signal(signal.SIGKILL, handle_signal)
	for p in processes:
		p.join()
