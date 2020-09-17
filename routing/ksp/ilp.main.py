from routing.ksp.ilp2 import ILPModel
from routing.instance import ILPInstance
from routing.instance import ILPInput
from routing.instance import ILPOutput
from typing import List, Tuple, Callable
from utils.log_utils import debug, info, err
from routing.ksp.ilp2 import NetworkTopo
from utils.time_utils import now_in_seconds

def map_func(fn: str) -> List[ILPInput]:
	'''
	read file specified by fn,generate ilpinput
	:param fn:
	:return:
	'''
	pass

def topo_loader(fn:str)->List[List[Tuple]]:
	'''
	load topo from file
	:param fn:
	:return:
	'''
	pass

def generate_labels(traffic_fn:str, topo_fn:str, traffic_loader_func:Callable[[str], List[ILPInput]],topo_loader_func:Callable[[str],List[List[Tuple]]])->List[ILPInstance]:
	'''
	:param traffic_fn:
	:param traffic_loader_func:
	:param output:
	:return:
	'''
	inputs:List[ILPInput]=traffic_loader_func(traffic_fn)
	topo=topo_loader_func(topo_fn)
	model=ILPModel(NetworkTopo(topo),0)
	output:List[ILPInstance]=[]
	for idx,inp in enumerate(inputs):
		start=now_in_seconds()
		out=model.solve(inp)
		end=now_in_seconds()
		info("Solve {}th problem use seconds {}".format(idx,end-start))
		instance=ILPInstance(video=inp.video,iot=inp.iot,voip=inp.voip,ar=inp.ar,labels={
			"video":out.video,
			"iot":out.iot,
			"ar":out.iot,
			"voip":out.voip
		})
		output.append(instance)
	return output



if __name__ == '__main__':
	pass
