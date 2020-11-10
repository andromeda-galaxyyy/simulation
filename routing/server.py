import json
from json import JSONDecodeError
import socketserver
from utils.common_utils import info
from sockets.server import Server, recvall2
from routing.nn.minor_predictor import MultiProcessPredictor
from common.graph import NetworkTopo
from routing.constant import topo_fn
from utils.file_utils import load_pkl
from routing.instance import RoutingInput
from utils.time_utils import now_in_milli
from utils.log_utils import debug
from typing import List

# info("All models loaded")
topo = NetworkTopo(load_pkl(topo_fn)[0])
ksp = {}
nodes = 66
K = 3

minor_predictor = MultiProcessPredictor(66)

src_dsts = [(s, d) for s in range(nodes) for d in range(nodes)]

src_dsts = list(filter(lambda x: x[0] != x[1], src_dsts))

for s, d in src_dsts:
	large_volume_paths = topo.ksp(s, d, K)
	low_latency_paths = topo.ksp(s, d, K, "delay")
	ksp[(s, d)] = (large_volume_paths, low_latency_paths)

info("ksp calculated")

idx_to_src_dst = [None for i in range(nodes * (nodes - 1))]

for i in range(nodes * (nodes - 1)):
	src = i // (nodes - 1)
	dst = i % (nodes - 1)
	if dst >= src: dst += 1
	idx_to_src_dst[i] = (src, dst)

info("idx to src_dst calculated")


def check(content: str):
	try:
		obj = json.loads(content)
	except JSONDecodeError:
		return -1
	if "volumes" not in list(obj.keys()):
		return -1
	volumes = obj["volumes"]
	if len(volumes) != nodes * (nodes - 1) * 2:
		return -1

	return volumes


n_flows = 4
n_src_dsts = nodes * (nodes - 1)


class MinorModelHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		# req_str = str(recvall2(request)), "ascii")
		req_str = recvall2(self.request)
		# vols = check(req_str)
		vols: List[int] = json.loads(req_str)["volumes"]
		shorted = False
		if len(vols) == 66 * 65 * 3:
			shorted = True
			vols.extend([0 for _ in range(66 * 65)])

		start = now_in_milli()

		video = vols[:n_src_dsts]
		iot = vols[n_src_dsts:2 * n_src_dsts]
		voip = vols[2 * n_src_dsts:3 * n_src_dsts]
		ar = vols[3 * n_src_dsts:]

		inpt = RoutingInput(video=video, iot=iot, voip=voip, ar=ar)

		output = minor_predictor(inpt)
		end = now_in_milli()
		info("Minor model predictor use {} milliseconds".format(end - start))

		# res = []
		res = {}
		# video
		video=[]
		for i in range(n_src_dsts):
			src_dst = idx_to_src_dst[i]
			large_volume_paths_, low_latency_paths_ = ksp[src_dst]
			video.append(large_volume_paths_[output.video[i]])
		res["res1"]=video
		iot=[]
		for i in range(n_src_dsts):
			src_dst = idx_to_src_dst[i]
			large_volume_paths_, low_latency_paths_ = ksp[src_dst]
			iot.append(low_latency_paths_[output.iot[i]])
		res["res2"]=iot

		voip=[]
		for i in range(n_src_dsts):
			src_dst = idx_to_src_dst[i]
			large_volume_paths_, low_latency_paths_ = ksp[src_dst]
			voip.append(low_latency_paths_[output.voip[i]])
		res["res3"]=voip

		if not shorted:
			for i in range(n_src_dsts):
				src_dst = idx_to_src_dst[i]
				large_volume_paths_, low_latency_paths_ = ksp[src_dst]
			# res.append(low_latency_paths_[output.ar[i]])

		# res = {"res": res}
		self.request.sendall(bytes(json.dumps(res), "ascii"))
		debug("response sent")


if __name__ == '__main__':
	port = 1030
	server = Server(port, MinorModelHandler)
	debug("routing server started")
	server.start()
