import json
from json import JSONDecodeError
import socketserver

from networkx.exception import NetworkXUnfeasible
from utils.log_utils import debug, info, err
from sockets.server import Server, recvall2
from common.graph import NetworkTopo
from utils.file_utils import load_pkl, load_json
from routing.nn3.models import *
from utils.time_utils import now_in_milli
from utils.log_utils import debug
from typing import List, Tuple, Dict
from routing.nn3.contants import *
from path_utils import get_prj_root
import os

# loading ksps

# cache_dir = os.path.join(get_prj_root(), "cache")
# static_dir = os.path.join(get_prj_root(), "static")
# ksp_obj = load_json(os.path.join(static_dir, "ksp.json"))["aksp"]
#
# ksps = {}
# for i in range(100):
# 	for j in range(100):
# 		if i == j:
# 			continue
# 		ksps[(i, j)] = ksp_obj[i][j]


from threading import Thread
import socket


class Predictor:
	def __init__(self):

		pass

	def _fetch_single_routing(self, model_id, traffic: List[float], res: List[int]):
		sock_fn = os.path.join("/tmp/{}.sock".format(model_id))
		client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		try:
			client.connect(sock_fn)
		except socket.error as msg:
			err(msg)
			exit(-1)
		req = {
			"volumes": traffic
		}
		client.sendall(bytes(json.dumps(req) + "*", "ascii"))
		try:
			resp = recvall2(client)
		finally:
			client.close()
		resp = json.loads(resp)
		actions = resp["res"]
		n_action = len(modelid_to_targets[model_id])
		actions = actions[:n_action]
		for idx, target in enumerate(modelid_to_targets[model_id]):
			action = actions[idx]
			flattened_idx = flattenidxes[(model_id, target)]
			res[flattened_idx] = action

	def __call__(self, inpt: RoutingInput):
		traffic = inpt.traffic
		res = [0 for _ in range(100 * 99)]
		threads = []
		for model_id in modelid_to_targets.keys():
			t = Thread(target=self._fetch_single_routing, args=(model_id, traffic, res))
			t.start()
			threads.append(t)
		for t in threads:
			t.join()
		out = RoutingOutput(labels=res)
		return out


predictor = Predictor()
import numpy as np


class RandomPredictor:
	def __init__(self):
		np.random.seed()

	def __call__(self, inpt: RoutingInput) -> RoutingOutput:
		res = [0 for _ in range(100 * 99)]
		for model_id in modelid_to_targets.keys():
			for target in modelid_to_targets[model_id]:
				res[flattenidxes[(model_id, target)]] = np.random.choice(list(range(5)))
		return RoutingOutput(labels=res)


random_predictor = RandomPredictor()


class NN3Server(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_content = recvall2(self.request)
		obj: Dict = {}
		try:
			obj = json.loads(req_content)
		except JSONDecodeError as e:
			err(obj)

		debug("traffic stats collected {}".format(len(obj["matrix"]["0"])))
		inpt = RoutingInput(traffic=obj["matrix"]["0"])
		if len(obj["matrix"]["0"]) != 100 * 99:
			err("invalid traffic matrix of len {}".format(len(obj["matrix"]["0"])))
			paths = []
			for i in range(100):
				for j in range(100):
					if i == j: continue
					paths.append(ksps[(i, j)][0])

			res = {"res1": paths}
			self.request.sendall(bytes(json.dumps(res) + "*", "ascii"))
			return

		routing:RoutingOutput=predictor(inpt)
		# routing: RoutingOutput = random_predictor(inpt)
		debug(len(routing.labels))
		paths = []
		for i in range(100):
			for j in range(100):
				if i == j: continue
				paths.append(ksps[(i, j)][routing.labels[flattenidxes[(i, j)]]])

		res = {"res1": paths}
		self.request.sendall(bytes(json.dumps(res) + "*", "ascii"))


if __name__ == '__main__':
	# labels_dir="/tmp/labels"
	# from routing.eval.evaluator3 import RoutingEvaluator3
	# from routing.nn3.contants import topo
	# evaluator=RoutingEvaluator3(topo)
	#
	# fns = []
	# for fn in os.listdir(labels_dir):
	# 	if "partition" not in fn: continue
	# 	fns.append(os.path.join(labels_dir, fn))
	# debug("number of fns {}".format(len(fns)))
	# fns.sort()
	# ilproutings:List[Routing]=[]
	# validate_fns=fns[int(len(fns)*0.9):]
	# debug("validate fns {}".format(len(validate_fns)))
	# for fn in validate_fns:
	# 	ilproutings.extend(load_pkl(fn))
	# import random
	# random.shuffle(ilproutings)
	# ilproutings=ilproutings[:500]
	#
	# debug("validate instances {}".format(len(ilproutings)))
	# ilp_ratios:List[float]=[]
	# nn_ratios:List[float]=[]
	# ospf_ratios:List[float]=[]
	# ratios_dir="/tmp/ratios"
	# # for idx,routing in enumerate(ilproutings):
	# # 	ilp_ratios.append(evaluator(routing))
	# # 	debug("ilp routing evaluate done {}".format(idx))
	# #
	# # debug("ilp ratios calculate done")
	# ilp_ratio_fn=os.path.join(ratios_dir,"ilp_ratios.pkl")
	# # save_pkl(ilp_ratio_fn,ilp_ratios)
	#
	# # for idx,routing in enumerate(ilproutings):
	# # 	inpt=RoutingInput(traffic=routing.traffic)
	# # 	out=predictor(inpt)
	# # 	instance=Routing(inpt.traffic,out.labels)
	# # 	nn_ratios.append(evaluator(instance))
	# # 	debug("nn routing {} evaluate done".format(idx))
	# nn_ratio_fn=os.path.join(ratios_dir,"nn_ratios.pkl")
	# # save_pkl(nn_ratio_fn,nn_ratios)
	#
	# action=[0 for _ in range(100*99)]
	# # for idx,routing in enumerate(ilproutings):
	# # 	ospf_ratios.append(evaluator(Routing(traffic=routing.traffic,labels=action)))
	# # 	debug("ospf evaluate done {}".format(idx))
	# ospf_ratio_fn=os.path.join(ratios_dir,"ospf_ratios.pkl")
	# # save_pkl(ospf_ratio_fn,ospf_ratios)
	# import matplotlib
	# matplotlib.use("TkAgg")
	# import matplotlib.pyplot as plt
	# ilpratios=load_pkl(ilp_ratio_fn)
	# nnratios=load_pkl(nn_ratio_fn)
	# ospfratios=load_pkl(ospf_ratio_fn)
	# ilp_plt,=plt.plot(ilpratios,label="ilp")
	# nn_plt,= plt.plot(nnratios,label="nn")
	# ospf_plt,=plt.plot(ospfratios,label="ospf")
	# plt.legend(handles=[ilp_plt,nn_plt,ospf_plt])
	# plt.show()

	# inpt=RoutingInput(traffic=[0 for _ in range(100*99)])
	# out=predictor(inpt)
	# debug(len(out.labels))
	port = 1055
	server = Server(port, NN3Server)
	debug("nn routing server started")
	server.start()
