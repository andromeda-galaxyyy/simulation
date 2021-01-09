from utils.log_utils import info, err, debug
from utils.file_utils import load_pkl, load_json
from typing import List, Dict, Tuple
from utils.num_utils import is_digit
from collections import defaultdict
import os
from path_utils import get_prj_root

static_dir = os.path.join(get_prj_root(), "static")
topo_fn = os.path.join(static_dir, "topo.json")
labels_fn = os.path.join(static_dir, "node_labels.json")
topo: List[List[Tuple[int, int, int, int]]] = None
labels: Dict = {}
net = defaultdict(set)
level1 = []
level2 = []
level3 = []


def cli():
	# nonlocal topo, labels,net,level3,level2,level1
	while True:
		try:
			print("input one node")
			ipt = input(">node:\n").strip()
			if not is_digit(ipt):
				print("not digit,re-input please")
				os.system("clear")
				continue
			node = int(ipt)
			if node > 99 or node < 0:
				print("invalid,re-input please")
			l = 1
			if node in level2:
				l = 2
			if node in level3:
				l = 3
			print("Level {}".format(l))
			print("Neighbors:")
			for n in net[node]:
				level = 1
				if n in level2:
					level = 2
				if n in level3:
					level = 3
				print("Neighbor:{}, Level {}".format(n, level))


		except KeyboardInterrupt:
			print("exit")
			exit(0)


if __name__ == '__main__':
	topo = load_json(topo_fn)["topo"]
	node_labels = load_json(labels_fn)
	# store labels
	level1 = node_labels["level1"]
	# level2=[]
	# level3=[]
	for content in node_labels["level2"]:
		level2.extend(content)
	for content in node_labels["level3"]:
		level3.extend(content)

	for i in range(100):
		for j in range(100):
			if i == j: continue
			if -1 not in topo[i][j]:
				net[i].add(j)
				net[j].add(i)
	cli()
