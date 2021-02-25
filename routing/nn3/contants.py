modelid_to_targets = {
	0: [18, 20, 22, 24, 26, 28, 40, 42, 44, 46, 48, 50],
	2: [18, 20, 22, 24, 26, 28, 40, 42, 44, 46, 48, 50],
	4: [18, 20, 22, 24, 26, 28, 40, 42, 44, 46, 48, 50],
	6: [62, 64, 66, 68, 70, 72, 84, 86, 88, 90, 92, 94],
	8: [62, 64, 66, 68, 70, 72, 84, 86, 88, 90, 92, 94],
	10: [62, 64, 66, 68, 70, 72, 84, 86, 88, 90, 92, 94],
	18: [40, 42, 44, 46, 48, 50, 33, 32, 31, 30, 29, 28, 27, 26],
	19: [40, 42, 44, 46, 48, 50, 33, 32, 31, 30, 29, 28, 27, 26],
	20: [40, 42, 44, 46, 48, 50, 33, 32, 31, 30, 29, 28, 27, 26],
}

idx = 0
flattenidxes = {}

for i in range(100):
	for j in range(100):
		if i == j: continue
		flattenidxes[(i, j)] = idx
		idx += 1

assert idx == 100 * 99

import os
from utils.file_utils import load_json, load_pkl
from path_utils import get_prj_root

cache_dir = os.path.join(get_prj_root(), "cache")
static_dir = os.path.join(get_prj_root(), "static")
ksp_obj = load_json(os.path.join(static_dir, "ksp.json"))["aksp"]

ksps = {}
for i in range(100):
	for j in range(100):
		if i == j:
			continue
		ksps[(i, j)] = ksp_obj[i][j]

topo = load_json(os.path.join(static_dir, "topo.json"))["topo"]
