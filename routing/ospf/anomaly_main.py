from typing import Dict, List, Tuple
from json import JSONDecodeError
from collections import namedtuple
import socketserver
from sockets.server import Server
from common.graph import NetworkTopo
from routing.nn3.contants import *
from utils.time_utils import now_in_milli
from routing.nn3.models import *
from path_utils import get_prj_root
from utils.log_utils import debug, info, err
import os
from utils.file_utils import load_json
from sockets.server import recvall2
from copy import deepcopy

topo_fn = os.path.join(get_prj_root(), "static/topo.json")
topo = load_json(topo_fn)["topo"]
anomaly_topo = deepcopy(topo)
anomaly_topo[2][5] = [-1, -1, -1, -1]
anomaly_topo[5][2] = [-1, -1, -1, -1]


net = NetworkTopo(topo)
debug(net.shortest_path(1, 10, "simple"))
anomaly_net: NetworkTopo = NetworkTopo(anomaly_topo)
debug(anomaly_net.shortest_path(1, 10, "simple"))


# for i in range(100):
# 	for j in range(100):
# 		if i==j:continue
# 		path=net.shortest_path(i,j,"simple")
# 		if (2,5) in zip(path[0:-1],path[1:]):
# 			debug(path)


class OSPF:
    def __init__(self, topo: NetworkTopo):
        self.net: NetworkTopo = topo
        self.paths = {}
        for i in range(100):
            for j in range(100):
                if i == j:
                    continue
                self.paths[(i, j)] = self.net.shortest_path(i, j, "simple")

    def reset(self):
        pass

    def __call__(self):
        out = []
        for i in range(100):
            for j in range(100):
                if i == j:
                    continue
                out.append(self.paths[(i, j)])
        return out


class AnomalyOSPF:
    def __init__(self, net: NetworkTopo) -> None:
        self.net = net
        # cache
        self.routings = {}
        for i in range(100):
            for j in range(100):
                if i == j:
                    continue
                self.routings[(i, j)] = self.net.shortest_path(i, j, "simple")

    def __call__(self) -> List[List[int]]:
        out = []
        for i in range(100):
            for j in range(100):
                if i == j:
                    continue
                out.append(self.routings[(i, j)])
        return out


ospf = OSPF(net)
anomaly_ospf = AnomalyOSPF(anomaly_net)


class OSPFHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        req_content = recvall2(self.request)
        if req_content == "default":
            debug("default routing")
            out = ospf()
        else:
            out = anomaly_ospf()
        # debug("ospf calculating use {} miliseconds".format(now_in_milli()-start))
        res = {
            "res1": out
        }
        ospf.reset()
        debug("reset done")
        self.request.sendall(bytes(json.dumps(res) + "*", "ascii"))


if __name__ == '__main__':
    # import numpy as np
    # ospf=OSPF(net)
    # inpt=RoutingInput(traffic=[np.random.randint(10,30) for _ in range(100*99)])
    # start=now_in_milli()
    # inpt=ospf(inpt)
    # debug(now_in_milli()-start)

    port = 1059
    server = Server(port, OSPFHandler)
    debug("anomaly server start")
    server.start()
