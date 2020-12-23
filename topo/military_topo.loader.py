from utils.file_utils import save_pkl, save_json
from utils.log_utils import info, debug
from common.graph import NetworkTopo

# 生成三级节点
node_labels = {"level1": list(range(12)),
               "level2": [
	               list(range(12, 18)),
	               list(range(34, 40)),
	               list(range(56, 62)),
	               list(range(78, 84))
               ],
               "level3": [
	               list(range(18, 34)),
	               list(range(40, 56)),
	               list(range(62, 78)),
	               list(range(84, 100))
               ]}

# 生成topo
topo = [[[-1, -1, -1, -1] for _ in range(100)] for _ in range(100)]
link = [100, 0, 0, 0]


def connect(i, j):
	global topo
	topo[i][j] = link
	topo[j][i] = link


# level1 内部连接
for idx, node in enumerate(node_labels["level1"]):
	n = len(node_labels["level1"])
	connect(idx, (idx + 1) % n)
	connect(idx, (idx + 11) % n)

import networkx as nx

g = nx.havel_hakimi_graph([4 for _ in range(12)])

for i in range(12):
	for j in range(12):
		if i == j: continue
		if j in g[i]:
			connect(i, j)

net = NetworkTopo(topo)
debug(net.g.number_of_edges())

# level2  内部连接
# 12*4=48
for idx, nodes in enumerate(node_labels["level2"]):
	n = len(nodes)
	assert n == 6
	start = nodes[0]
	for idx, node in enumerate(nodes):
		connect(node, start + (idx + 1) % n)
		connect(node, start + (idx + 5) % n)

	connect(start, start + 2)
	connect(start, start + 4)
	connect(start + 1, start + 3)
	connect(start + 1, start + 5)
	connect(start + 5, start + 3)
	connect(start + 4, start + 2)

# level1 与level2连接
# 4*4=16
nodes = node_labels["level2"][0]
n = len(nodes)
start = nodes[0]
connect(start, 0)
connect(start + 1, 3)
connect(start + 2, 6)
connect(start + 4, 9)

nodes = node_labels["level2"][1]
n = len(nodes)
start = nodes[0]
connect(start, 1)
connect(start + 1, 4)
connect(start + 2, 7)
connect(start + 4, 10)

nodes = node_labels["level2"][2]
n = len(nodes)
start = nodes[0]
connect(start, 2)
connect(start + 1, 5)
connect(start + 2, 8)
connect(start + 4, 11)

nodes = node_labels["level2"][3]
n = len(nodes)
start = nodes[0]
connect(start, 0)
connect(start + 1, 3)
connect(start + 2, 6)
connect(start + 4, 9)

# net = NetworkTopo(topo)
# debug(net.g.number_of_edges())

# level3 与level2连接
for idx, nodes in enumerate(node_labels["level3"]):
	assert len(nodes) == 16
	start = nodes[0]
	level2_start = nodes[0] - 6
	for node in nodes:
		connect(node, level2_start + (node - start) % 6)
		connect(node, level2_start + ((node - start) % 6 + 2) % 6)
		connect(node, level2_start + ((node - start) % 6 + 4) % 6)
# debug(topo)

count = 0
for i in range(len(topo)):
	for j in range(len(topo[0])):
		if -1 not in topo[i][j]:
			count += 1

debug(count)
net = NetworkTopo(topo)
# topo.plot()
net.plot()
# import netgraph
# netgraph.draw(net.g)
debug(net.g.number_of_edges())

from path_utils import get_prj_root
import os

static_dir = os.path.join(get_prj_root(), "static")
save_json(os.path.join(static_dir,"topo.json"),{"topo":topo})

res = []
for _ in range(44):
	res.append({
		"topo": topo,
		"duration": 0
	})

save_json(os.path.join(static_dir, "node_labels.json"), node_labels)
save_pkl(os.path.join(static_dir, "military.pkl"), res)
