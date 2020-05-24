import networkx as nx
from py2_utils import save_json,get_prj_root
import os
nodes = 9
K = 3
g= nx.grid_graph([3, 3])
g = nx.relabel_nodes(g, lambda x: x[0] * K + x[1])

topo=[[[-1,-1,-1,-1] for _ in range(nodes)] for _ in range(nodes)]

for i in range(nodes):
	for j in range(nodes):
		if i==j:continue
		if g.has_edge(i,j):
			topo[i][j]=[1,1,1,1]

topo_dir=os.path.join(get_prj_root(),"files")

res={
	"topo":topo
}
save_json(os.path.join(topo_dir,"demo.json"),res)


