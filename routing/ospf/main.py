import socketserver
from sockets.server import Server
from common.graph import NetworkTopo
from routing.nn3.contants import *
from utils.time_utils import now_in_milli
from routing.nn3.models import *
from path_utils import get_prj_root
from utils.log_utils import debug,info,err
import os
from utils.file_utils import load_json
from sockets.server import recvall2

topo_fn=os.path.join(get_prj_root(),"static/topo.json")
topo=load_json(topo_fn)["topo"]

from collections import namedtuple
from typing import Dict,List,Tuple
from json import JSONDecodeError


net=NetworkTopo(topo)

class OSPF:
	def __init__(self,topo:NetworkTopo):
		self.net:NetworkTopo=topo
		for u,v,d in self.net.g.edges(data=True):
			self.net.add_edge_attr(u,v,"remain",1e5)
			self.net.add_edge_attr(u,v,"w",1/1e5)
			self.net.add_edge_attr(u,v,"simple",1)

	def reset(self):
		for u,v,d in self.net.g.edges(data=True):
			self.net.add_edge_attr(u,v,"remain",1e5)
			self.net.add_edge_attr(u,v,"w",1/1e5)


	def __call__(self, inpt:RoutingInput):
		traffic=inpt.traffic
		#find max
		ma=max(traffic)
		if ma==0:
			paths=[]
			for i in range(100):
				for j in range(100):
					if i==j:continue
					paths.append(ksps[(i,j)][0])
			return paths
		traffic=[t/ma for t in traffic]
		paths={}
		src_dsts=[]
		for i in range(100):
			for j in range(100):
				if i==j:continue
				src_dsts.append((i,j))

		for s,d in src_dsts:
			# t=traffic[flattenidxes[(s,d)]]
			# p=self.net.shortest_path(s,d,"w")
			paths[(s,d)]=self.net.shortest_path(s,d,"simple")
			# #update weight
			# for u,v,d in self.net.g.edges(data=True):
			# 	if self.net.edge_in_path(u,v,p):
			# 		oldv=self.net.get_edge_attr(u,v,"remain")
			# 		newv=oldv-t
			# 		self.net.add_edge_attr(u,v,"remain",newv)
			# 		self.net.add_edge_attr(u,v,"w",1/newv)

		# out=RoutingOutput(labels=[0 for _ in range(100*99)])
		out=[]
		for i in range(100):
			for j in range(100):
				if i==j:continue
				out.append(paths[(i,j)])
		return out


ospf=OSPF(net)

class OFPFHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_content = recvall2(self.request)
		obj: Dict = {}
		try:
			obj = json.loads(req_content)
		except JSONDecodeError as e:
			err(obj)

		debug("traffic stats collected {}".format(len(obj["matrix"]["0"])))
		inpt = RoutingInput(traffic=obj["matrix"]["0"])
		start=now_in_milli()
		out=ospf(inpt)
		debug("ospf calculating use {} miliseconds".format(now_in_milli()-start))
		res={
			"res1":out
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

	port=1055
	server=Server(port,OFPFHandler)
	debug("ospf server start")
	server.start()