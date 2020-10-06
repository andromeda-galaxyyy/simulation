from utils.file_utils import *
from utils.log_utils import *
from routing.instance import *
from typing import Tuple, List, Dict
from routing.nn.minor import Minor
import numpy as np
from routing.nn.common import persist_dir
from routing.nn.minor import Minor
from path_utils import get_prj_root
import tensorflow as tf
from routing.nn.common import persist_dir, topo_fn
from multiprocessing import Process
from multiprocessing import Pool
from utils.time_utils import now_in_milli
import socketserver
from sockets.server import Server, recvall2
import json
import socket
from threading import Thread

default_topo = load_pkl(topo_fn)[0]


class Predictor:
	def _load_models(self, model_dir: str):
		# with tf.device("/cpu:0"):
		for idx in range(len(self.topo[0])):
			# for idx in range():
			fn = os.path.join(model_dir, "minor.{}.hdf5".format(idx))
			assert file_exsit(fn)
			model = Minor(idx, 66, 4, 3)
			model.load_model(fn)
			debug("loaded {} model".format(idx))
			self.models.append(model)

	def __init__(self, model_dir: str = persist_dir, topo: List[List[Tuple]] = default_topo):
		self.topo: List[List[Tuple]] = topo
		self.models: List[Minor] = []
		self._load_models(model_dir)
		self.pool = Pool(len(self.topo[0]))

	def __predict_single_model(self, model_id, traffic_matrix, video_actions, iot_actions,
	                           voip_actions, ar_actions):
		# traffic_matrix = np.asarray([traffic_matrix])
		n_nodes = len(self.topo[0])
		actions = self.models[model_id].predict(traffic_matrix)[0].tolist()

		video = actions[0]
		iot = actions[1]
		voip = actions[2]
		ar = actions[3]

		for idx in range(n_nodes - 1):
			idx_in_all_actions = model_id * (n_nodes - 1) + idx
			video_actions[idx_in_all_actions] = video[idx]
			iot_actions[idx_in_all_actions] = iot[idx]
			voip_actions[idx_in_all_actions] = voip[idx]
			ar_actions[idx_in_all_actions] = ar[idx]

		return 0

	def __call__(self, inpt: RoutingInput) -> RoutingOutput:
		traffic_matrix = []
		# map input to minor model input
		traffic_matrix.extend(inpt.video)
		traffic_matrix.extend(inpt.iot)
		traffic_matrix.extend(inpt.voip)
		traffic_matrix.extend(inpt.ar)
		traffic_matrix = np.asarray([traffic_matrix])

		n_nodes = len(self.topo[0])

		video_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]
		iot_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]
		voip_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]
		ar_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]

		for model_id in range(n_nodes):
			self.__predict_single_model(model_id, traffic_matrix, video_actions, iot_actions,
			                            voip_actions, ar_actions)

		return RoutingOutput(video=video_actions, iot=iot_actions, voip=voip_actions, ar=ar_actions)


def test_load():
	models = []

	with tf.device('/cpu:0'):
		# 	# new_model = load_model('test_model.h5')
		for model_id in range(66):
			model = Minor(model_id, 66, 4, 3)
			model.load_model()
			models.append(model)
			debug("load {} model".format(model_id))


class MultiProcessPredictor:
	def fetch_single_model_res(self, model_id: int, traffic_matrix: List[float], video_actions,
	                           iot_actions, voip_actions, ar_actions):
		client = self.clients[model_id]
		sock_fn = os.path.join("/tmp", "minor.{}.sock".format(model_id))
		try:
			client.connect(sock_fn)
			debug("connected to {}".format(sock_fn))
		except socket.error as msg:
			err(msg)
			exit(-1)

		req = {"volumes": traffic_matrix}

		client.sendall(bytes(json.dumps(req) + "*", "ascii"))
		resp = recvall2(client)
		client.close()
		debug("client received done")
		# debug(resp)
		resp = json.loads(resp)
		n_nodes=self.n_nodes

		for idx in range(n_nodes - 1):
			idx_in_all_actions = model_id * (n_nodes - 1) + idx
			video_actions[idx_in_all_actions] = resp["video"][idx]
			iot_actions[idx_in_all_actions] = resp["iot"][idx]
			voip_actions[idx_in_all_actions] = resp["voip"][idx]
			ar_actions[idx_in_all_actions] = resp["ar"][idx]
		return 0

	def __init__(self, n_nodes: int):
		self.clients = []
		self.n_nodes = n_nodes
		for _ in range(self.n_nodes):
			self.clients.append(socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))

	def __call__(self, inpt: RoutingInput) -> RoutingOutput:
		traffic_matrix = []
		# map input to minor model input
		traffic_matrix.extend(inpt.video)
		traffic_matrix.extend(inpt.iot)
		traffic_matrix.extend(inpt.voip)
		traffic_matrix.extend(inpt.ar)
		# traffic_matrix = np.asarray([traffic_matrix])

		n_nodes = self.n_nodes

		video_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]
		iot_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]
		voip_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]
		ar_actions = [0 for _ in range(n_nodes * (n_nodes - 1))]
		threads = []

		for model_id in range(66):
			t = Thread(target=self.fetch_single_model_res, args=(
				model_id, traffic_matrix, video_actions, iot_actions, voip_actions, ar_actions))
			t.start()
			threads.append(t)

		for t in threads:
			t.join()
		return RoutingOutput(video=video_actions, iot=iot_actions, voip=voip_actions, ar=ar_actions)


def test_predictor():
	predictor = MultiProcessPredictor(66)
	traffic_matrix = [100 for _ in range(66 * 65)]
	inp = RoutingInput(video=traffic_matrix, iot=traffic_matrix, voip=traffic_matrix,
	                   ar=traffic_matrix)
	start = now_in_milli()
	output = predictor(inp)
	debug("used {} milliseconds".format(now_in_milli() - start))


if __name__ == '__main__':
	test_predictor()



