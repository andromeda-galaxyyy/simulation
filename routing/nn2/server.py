from utils.log_utils import info, err, debug, warn
from utils.file_utils import load_pkl, load_json, save_json
import os
from path_utils import get_prj_root
from utils.file_utils import static_dir
from socketserver import BaseRequestHandler
from sockets.server import recvall2, Server
from typing import Dict, List, Tuple
import json
from threading import Thread
import socket

topo_fn = os.path.join(static_dir, "military.topo.json")
topo = load_json(topo_fn)["topo"]
input_demo_fn = os.path.join(get_prj_root(), "routing/nn2/static/input.json")
config_fn = os.path.join(get_prj_root(), "routing/nn2/static/config.json")
config = load_json(config_fn)

ksp_fn = os.path.join(get_prj_root(), "routing/nn2/static/ksp.json")
ksps = load_json(ksp_fn)["aksp"]

idx = 0
# debug("existing models {}".format(config["models"]))
model_key_to_idx = {}

link_utility = {}
for i in range(len(topo)):
	for j in range(len(topo[0])):
		if i == j: continue
		key = "{}-{}".format(i, j)
		model_key_to_idx[key] = idx
		idx += 1


class NNServer(BaseRequestHandler):
	def _fetch_single_model(self, link_rate: List[int], model_key: str, res_idx: int,
	                        res: List[int]):
		debug(len(link_rate))
		addr = config["models"][model_key]
		client=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
		sock_fn=addr["endpoint"]

		try:
			client.connect(sock_fn)
		except socket.error as msg:
			err(msg)
		except:
			exit(-1)
		req={
			"rates":link_rate
		}
		client.sendall(bytes(json.dumps(req)+"*","ascii"))
		try:
			resp=recvall2(client)
		finally:
			client.close()
		resp=json.loads(resp)
		res[res_idx] = resp["res"]
		debug("routing for model {} calculated".format(model_key))

	def handle(self) -> None:
		req_str = recvall2(self.request)
		# debug(req_str)
		req: Dict = None
		try:
			req = json.loads(req_str)
		except Exception as e:
			err(e)
			return
		# req received
		if len(req.keys()) != 283:
			err("Invalid requests")
			return
		# valid req obj
		link_rate = []
		for i in range(len(topo)):
			for j in range(len(topo)):
				if i >= j: continue
				if -1 in topo[i][j]: continue
				key = "{}-{}".format(i, j)
				if key not in req.keys():
					err("invalid req,key {} not found".format(key))
					return
				link_rate.append(req[key])

		threads: List[Thread] = []

		routing_path_idxs = [0 for _ in range(100 * 99)]
		for model_idx, model_key in enumerate(config["models"].keys()):
			t = Thread(target=self._fetch_single_model,
			           args=(link_rate, model_key, model_key_to_idx[model_key], routing_path_idxs))
			t.start()
			threads.append(t)

		for t in threads:
			t.join()

		debug("all paths fetched")
		resp = {
			"res1": []
		}
		ii = 0
		for i in range(len(topo)):
			for j in range(len(topo[0])):
				if i == j: continue
				resp["res1"].append(ksps[i][j][routing_path_idxs[ii]])
				ii += 1

		self.request.sendall(bytes(json.dumps(resp) + "*", "ascii"))


if __name__ == '__main__':
	server = Server(7788, NNServer)
	server.start()
