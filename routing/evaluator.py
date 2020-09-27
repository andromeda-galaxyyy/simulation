from utils.file_utils import *
from utils.log_utils import debug,info,err
from typing import List,Dict,Tuple
from routing.instance import *
from common.Graph import NetworkTopo

#todo implementation
class RoutingEvaluator:
	def __init__(self,topo:List[List[Tuple]],K:int):
		self.topo:List[List[Tuple]]=topo
		self.k=K


	def __call__(self, inpt:RoutingInput)->float:
		return 0



