from utils.file_utils import *
from utils.log_utils import *
from routing.instance import *
from typing import Tuple, List, Dict
from routing.nn.minor import Minor
import numpy as np
from routing.nn.common import persist_dir
from routing.nn.minor import Minor
from path_utils import get_prj_root


class Predictor:
	def _load_models(self, model_dir: str):
		for idx in range(len(self.topo[0])):
			fn = os.path.join(model_dir, "minor.{}.hdf5".format(idx))
			assert file_exsit(fn)
			model = Minor(idx, 66, 4, 3)
			model.load_model(fn)
			self.models.append(model)

	def __init__(self, model_dir: str, topo: List[List[Tuple]]):
		self.topo: List[List[Tuple]] = topo
		self.models: List[Minor] = []
		self._load_models(model_dir)

	def __call__(self, inpt: RoutingInput) -> RoutingOutput:
		traffic_matrix = []
		# map input to minor model input
		traffic_matrix.extend(inpt.video)
		traffic_matrix.extend(inpt.iot)
		traffic_matrix.extend(inpt.voip)
		traffic_matrix.extend(inpt.ar)
		traffic_matrix = np.asarray([traffic_matrix])

		video_actions = []
		iot_actions = []
		voip_actions = []
		ar_actions = []

		for model in self.models:
			actions = model.predict(traffic_matrix)[0].tolist()
			video_actions.extend(actions[0])
			iot_actions.extend(actions[1])
			voip_actions.extend(actions[2])
			ar_actions.extend(actions[3])

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



if __name__ == '__main__':
	pass