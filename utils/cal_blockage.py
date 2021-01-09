from path_utils import get_prj_root
from utils.file_utils import load_json
import os
from utils.log_utils import debug
from collections import defaultdict

static_dir = os.path.join(get_prj_root(), "static")
topo = load_json(os.path.join(static_dir, "topo.json"))["topo"]
node_labels = []

default_routing = load_json(os.path.join(static_dir, "military.default_routing.json"))["default"]
# debug(default_routing["default"])

ijtoidx={}
idx=0
for i in range(100):
	for j in range(100):
		if i==j:continue
		ijtoidx[(i,j)]=idx
		idx+=1

# 节点对->link
routing = defaultdict(set)
link_usage = defaultdict(set)
for i in range(100):
	for j in range(100):
		if i==j:continue
		idx=ijtoidx[(i,j)]
		path=default_routing[idx]
		for u,v in zip(path[0:-1],path[1:]):
			routing[(i,j)].add((u,v))
			link_usage[(u,v)].add((i,j))

# link->节点对
max_usage=-1
max_usage_link=None
#
for u,v in link_usage.keys():
	if max_usage<len(link_usage[(u,v)]):
		max_usage=len(link_usage[(u,v)])
		max_usage_link=(u,v)


print(max_usage_link)
print(max_usage)


