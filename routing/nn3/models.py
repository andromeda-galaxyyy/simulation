from collections import namedtuple
from utils.file_utils import save_pkl, load_pkl
from utils.log_utils import debug, info
from typing import Callable, Any, List
from utils.container_utils import shuffle_list
from collections import Counter
from utils.file_utils import read_lines
import json


Routing=namedtuple("Routing",["traffic","labels"])
RoutingInput=namedtuple("RoutingInput",["traffic"])
RoutingOutput=namedtuple("RoutingOutput",["labels"])

def load_routing_instances(fn:str):
	res:List[RoutingInput]=[]
	lines=read_lines(fn)
	for l in lines:
		obj=json.loads(l)
		res.append(RoutingInput(traffic=obj["0"]))
	return res


if __name__ == '__main__':
	load_routing_instances("/tmp/matrix1.txt")