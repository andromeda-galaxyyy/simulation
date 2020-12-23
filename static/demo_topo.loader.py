from utils.file_utils import save_pkl, save_json
from utils.log_utils import info, debug
from common.graph import NetworkTopo

# 生成topo
topo = [[[-1, -1, -1, -1] for _ in range(3)] for _ in range(3)]
link = [100, 0, 0, 0]




def connect(i, j):
	global topo
	topo[i][j] = link
	topo[j][i] = link

connect(0,1)
connect(1,2)



from path_utils import get_prj_root
import os

static_dir = os.path.join(get_prj_root(), "static")
# save_json(os.path.join(static_dir,"topo.json"),{"topo":topo})

res = []
for _ in range(44):
	res.append({
		"topo": topo,
		"duration": 0
	})

save_pkl(os.path.join(static_dir, "demo.pkl"), res)
