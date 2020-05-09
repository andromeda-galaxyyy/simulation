import sys

import networkx as nx

sys.path.append("../")
from utils import load_pkl, is_digit
from collections import defaultdict
from itertools import islice

def k_shortest_paths(G, source, target, k):
    return list(islice(nx.shortest_simple_paths(G, source, target), k))


topos = load_pkl('delaygraph_py2_v2.txt')
NUM_TOPOS = len(topos)
NUM_SATALLITES = len(topos[0])

links=set()

stats=defaultdict(list)
def link_state(topo, i, j):
    if (topo[i][j] == 0 or topo[i][j] is None):
        return False
    if (is_digit(topo[i][j])):
        return float(topo[i][j])
    return False

def is_connected(topo,i,j):
    if topo[i][j]==0 or topo[i][j] is None:
        return False
    return True

def check_graph(idx):
    print(idx)
    topo = topos[idx]
    g = nx.Graph()
    assert len(topo) == NUM_SATALLITES
    g.add_nodes_from(list(range(NUM_SATALLITES)))
    for i in range(NUM_SATALLITES):
        for j in range(NUM_SATALLITES):
            if is_connected(topo, i, j):
                links.add((i,j))
                g.add_edge(i, j,weight=1)

    for i in range(NUM_SATALLITES):
        for j in range(i + 1, NUM_SATALLITES):
            # print(i,j)
            paths=k_shortest_paths(g,i,j,10)
            assert len(paths)==10


            stats[len(paths)].append((idx,(i,j)))



for idx in range(NUM_TOPOS):
    check_graph(idx)

for k,v in stats.items():
    print("paths nums {} there is {} scenario".format(k,len(v)))

print(len(links))

#分析

