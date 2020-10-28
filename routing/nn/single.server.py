from utils.file_utils import *
from routing.instance import *
import numpy as np
from routing.nn.minor import Minor
from path_utils import get_prj_root
from routing.common import topo_fn
from sockets.server import recvall2
import json
import socket
from utils.time_utils import now_in_milli

default_topo = load_pkl(topo_fn)[0]


class SinglePredictor:
	def __init__(self, id_: int):
		self.model: Minor = Minor(id_, 66, 4, 3)
		self.model.load_model(
			os.path.join(get_prj_root(), "routing", "nn", "hdf5.5.3", "minor.{}.hdf5".format(id_)))

	def __call__(self, inpt: RoutingInput) -> RoutingOutput:
		traffic_matrix = []
		traffic_matrix.extend(inpt.video)
		traffic_matrix.extend(inpt.iot)
		traffic_matrix.extend(inpt.voip)
		traffic_matrix.extend(inpt.ar)
		traffic_matrix = np.asarray([traffic_matrix])

		actions = self.model.predict(traffic_matrix)[0].tolist()

		video = actions[0]
		iot = actions[1]
		voip = actions[2]
		ar = actions[3]
		return RoutingOutput(
			video=video,
			iot=iot,
			voip=voip,
			ar=ar
		)

def test_single_predictor():
	model=SinglePredictor(0)
	tmp=[1 for _ in range(66*65)]
	inpt=RoutingInput(video=tmp,ar=tmp,iot=tmp,voip=tmp)
	start=now_in_milli()
	model(inpt)
	debug("used {} milliseconds",now_in_milli()-start)

	start=now_in_milli()
	model(inpt)
	debug("used {} milliseconds",now_in_milli()-start)



class SinglePredictorServer:
	def __init__(self, model_id: int, predictor: SinglePredictor):
		sock_fn = os.path.join("/tmp", "minor.{}.sock".format(model_id))
		if os.path.exists(sock_fn):
			os.remove(sock_fn)
		self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.server.bind(sock_fn)
		self.predictor: SinglePredictor = predictor
		self.model_id = model_id

	def start(self):
		self.server.listen()
		debug("SinglePredictor Server for model {} is listening".format(self.model_id))
		while True:
			conn, _ = self.server.accept()
			debug("new connection")
			req = recvall2(conn)
			debug("received done")
			volumes = json.loads(req)["volumes"]
			inpt = RoutingInput(
				video=volumes[:66 * 65],
				iot=volumes[66 * 65:2 * 66 * 65],
				voip=volumes[2 * 66 * 65:3 * 66 * 65],
				ar=volumes[3 * 66 * 65:]
			)
			# convert volumes to
			output = self.predictor(inpt)
			resp = output_todict(output)
			conn.sendall(bytes(json.dumps(resp) + "*", "ascii"))
			conn.close()


if __name__ == '__main__':
	# import argparse

	# parser = argparse.ArgumentParser()
	# parser.add_argument("--id", type=int, default=0)
	# args = parser.parse_args()

	# model_id = int(args.id)
	# model = Minor(model_id, 66, 4, 3)

	# server = SinglePredictorServer(model_id, SinglePredictor(model_id))
	# server.start()
	test_single_predictor()
