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

default_topo = load_pkl(topo_fn)[0]


class Predictor:
	def _load_models(self, model_dir: str):
		for idx in range(len(self.topo[0])):
			fn = os.path.join(model_dir, "minor.{}.hdf5".format(idx))
			assert file_exsit(fn)
			model = Minor(idx, 66, 4, 3)
			model.load_model(fn)
			self.models.append(model)

	def __init__(self, model_dir: str = persist_dir, topo: List[List[Tuple]] = default_topo):
		self.topo: List[List[Tuple]] = topo
		self.models: List[Minor] = []
		self._load_models(model_dir)

	def __predict_single_model(self,model_id,traffic_matrix,video_actions,iot_actions,voip_actions,ar_actions):
		n_nodes=len(self.topo[0])
		actions=self.models[model_id].predict(traffic_matrix)[0].tolist()

		video = actions[0]
		iot=actions[1]
		voip=actions[2]
		ar=actions[3]

		for idx in range(n_nodes-1):
			idx_in_all_actions=model_id*(n_nodes-1)+idx
			video_actions[idx_in_all_actions]=video[idx]
			iot_actions[idx_in_all_actions]=iot[idx]
			voip_actions[idx_in_all_actions]=voip[idx]
			ar_actions[idx_in_all_actions]=ar[idx]

	def __call__(self, inpt: RoutingInput) -> RoutingOutput:
		traffic_matrix = []
		# map input to minor model input
		traffic_matrix.extend(inpt.video)
		traffic_matrix.extend(inpt.iot)
		traffic_matrix.extend(inpt.voip)
		traffic_matrix.extend(inpt.ar)
		traffic_matrix = np.asarray([traffic_matrix])

		n_nodes=len(self.topo[0])

		video_actions = [0 for _ in range(n_nodes)]
		iot_actions = [0 for _ in range(n_nodes)]
		voip_actions = [0 for _ in range(n_nodes)]
		ar_actions = [0 for _ in range(n_nodes)]
		processes=[]

		for model_id in range(len(self.models)):
			process=Process(target=self.__predict_single_model,args=(model_id,traffic_matrix,video_actions,iot_actions,voip_actions,ar_actions))
			process.start()
			processes.append(process)

		for p in processes:
			p.join()

		return RoutingOutput(video=video_actions, iot=iot_actions, voip=voip_actions, ar=ar_actions)


class SinglePredictor:
	def __init__(self, id_: int):
		self.model: Minor = Minor(id_, 66, 4, 3)
		self.model.load_model()

	def __call__(self, *args, inpt: RoutingInput):
		traffic_matrix = []
		traffic_matrix.extend(inpt.video)
		traffic_matrix.extend(inpt.iot)
		traffic_matrix.extend(inpt.voip)
		traffic_matrix.extend(inpt.ar)
		traffic_matrix = np.asarray([traffic_matrix])

		actions = self.model.predict(traffic_matrix)[0].tolist()
		return actions


def test_load():
	models = []

	with tf.device('/cpu:0'):
		# 	# new_model = load_model('test_model.h5')
		for model_id in range(66):
			model = Minor(model_id, 66, 4, 3)
			model.load_model()
			models.append(model)
			debug("load {} model".format(model_id))


if __name__ == '__main__':
	test_load()
