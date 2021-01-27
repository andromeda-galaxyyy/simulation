# import writeCommands as wt
# import calculate_monitor as cm
import copy
import json
from utils.file_utils import load_json
from path_utils import get_prj_root
import os
from utils.file_utils import load_pkl, save_pkl
'''
with open("/tmp/topo.json",'r') as f:
	topo=json.load(f)["topo"]
vars={}
vlan_to_link = {}
link_to_vlan = {}
num = 1
for i in range(len(topo)):
	for j in range(len(topo[i])):
		if -1 in topo[i][j]:
			continue
		vlan_to_link[num] = (1+i, 1+j)
		link_to_vlan[(i+1, j+1)] = num
		num += 1
vlan_to_link[num] = (23, 0)
link_to_vlan[(23, 0)] = num
vars = {"vlan_to_link": vlan_to_link,
             "link_to_vlan": link_to_vlan}
print(vars["link_to_vlan"])
# with open("link_to_vlan.json", 'w') as f:
# 	json.dump(link_to_vlan, f)
from path_utils import get_prj_root
from utils.file_utils import save_pkl,load_pkl
save_pkl("/tmp/vars.pkl",vars)
vars_reloaded=load_pkl("/tmp/vars.pkl")
g = cm.makeTopo(topo)
# self.vars["edge_port"]=edge_port
print("拓扑边集：")
# print(type(g.edges))
print(list(g.edges)[:len(g.edges) // 2])
print(list(g.edges)[len(g.edges) // 2:])

location = cm.Biding(g.edges, g)
result=location.biding_strategy()
if result[0]==-1:
	print(result)
elif result[0]==0:
	vars["monitor"]=result[1]
	vars["paths"]=result[2]
	vars["recv_num"]=result[3]
switches = 66
edge=[]
for link in g.edges:
	edge.append(link)
t = wt.table(edge,vars["paths"], switches,vars["monitor"],vars["link_to_vlan"])
flow_table=t.make_res()
print(flow_table)

{(1, 2): 1, (1, 11): 2, (1, 12): 3, (2, 1): 4, (2, 3): 5, 
 (2, 13): 6, (3, 2): 7, (3, 4): 8, (4, 3): 9, (4, 5): 10, 
 (5, 4): 11, (5, 6): 12, (5, 16): 13, (6, 5): 14, (6, 7): 15, 
 (6, 17): 16, (7, 6): 17, (7, 8): 18, (7, 18): 19, (8, 7): 20, 
 (8, 9): 21, (8, 19): 22, (9, 8): 23, (9, 10): 24, (10, 9): 25, 
 (10, 11): 26, (11, 1): 27, (11, 10): 28, (11, 22): 29, (12, 1): 30,
 (12, 13): 31, (12, 22): 32, (12, 23): 33, (13, 2): 34, (13, 12): 35,
 (13, 14): 36, (13, 24): 37, (14, 13): 38, (14, 15): 39, (15, 14): 40,
 (15, 16): 41, (16, 5): 42, (16, 15): 43, (16, 17): 44, (16, 27): 45,
 (17, 6): 46, (17, 16): 47, (17, 18): 48, (17, 28): 49, (18, 7): 50,
 (18, 17): 51, (18, 19): 52, (18, 29): 53, (19, 8): 54, (19, 18): 55,
 (19, 20): 56, (19, 30): 57, (20, 19): 58, (20, 21): 59, (21, 20):60,
 (21, 22): 61, (22, 11): 62, (22, 12): 63, (22, 21): 64, (22, 33):65,
 (23, 12): 66, (23, 24): 67, (23, 33): 68, (23, 34): 69, (24, 13):70,
 (24, 23): 71, (24, 25): 72, (24, 35): 73, (25, 24): 74, (25, 26):75,
 (26, 25): 76, (26, 27): 77, (27, 16): 78, (27, 26): 79, (27, 28):80,
 (27, 38): 81, (28, 17): 82, (28, 27): 83, (28, 29): 84, (28, 39): 85,
 (29, 18): 86, (29, 28): 87, (29, 30): 88, (29, 40): 89, (30, 19): 90,
 (30, 29): 91, (30, 31): 92, (30, 41): 93, (31, 30): 94, (31, 32): 95,
 (32, 31): 96, (32, 33): 97, (33, 22): 98, (33, 23): 99, (33, 32): 100,
 (33, 44): 101, (34, 23): 102, (34, 35): 103, (34, 44): 104, 
 (34, 45): 105, (35, 24): 106, (35, 34): 107, (35, 36): 108, 
 (35, 46): 109, (36, 35): 110, (36, 37): 111, (37, 36): 112, 
 (37, 38): 113, (38, 27): 114, (38, 37): 115, (38, 39): 116, 
 (38, 49): 117, (39, 28): 118, (39, 38): 119, (39, 40): 120, 
 (39, 50): 121, (40, 29): 122, (40, 39): 123, (40, 41): 124, 
 (40, 51): 125, (41, 30): 126, (41, 40): 127, (41, 42): 128, 
 (41, 52): 129, (42, 41): 130, (42, 43): 131, (43, 42): 132, 
 (43, 44): 133, (44, 33): 134, (44, 34): 135, (44, 43): 136, 
 (44, 55): 137, (45, 34): 138, (45, 46): 139, (45, 55): 140, 
 (45, 56): 141, (46, 35): 142, (46, 45): 143, (46, 47): 144, 
 (46, 57): 145, (47, 46): 146, (47, 48): 147, (48, 47): 148, 
 (48, 49): 149, (49, 38): 150, (49, 48): 151, (49, 50): 152, 
 (49, 60): 153, (50, 39): 154, (50, 49): 155, (50, 51): 156, 
 (50, 61): 157, (51, 40): 158, (51, 50): 159, (51, 52): 160, 
 (51, 62): 161, (52, 41): 162, (52, 51): 163, (52, 53): 164, 
 (52, 63): 165, (53, 52): 166, (53, 54): 167, (54, 53): 168, 
 (54, 55): 169, (55, 44): 170, (55, 45): 171, (55, 54): 172, 
 (55, 66): 173, (56, 45): 174, (56, 57): 175, (56, 66): 176, 
 (57, 46): 177, (57, 56): 178, (57, 58): 179, (58, 57): 180, 
 (58, 59): 181, (59, 58): 182, (59, 60): 183, (60, 49): 184, 
 (60, 59): 185, (60, 61): 186, (61, 50): 187, (61, 60): 188, 
 (61, 62): 189, (62, 51): 190, (62, 61): 191, (62, 63): 192, 
 (63, 52): 193, (63, 62): 194, (63, 64): 195, (64, 63): 196, 
(64, 65): 197, (65, 64): 198, (65, 66): 199, 
 (66, 55): 200, (66, 56): 201, (66, 65): 202, (23, 0): 203}
'''

with open("/tmp/topo.json", 'r') as f:
	topo = json.load(f)["topo"]
vars = {}
vlan_to_link = {}
link_to_vlan = {}
num = 1
for i in range(len(topo)):
	for j in range(len(topo[i])):
		if -1 in topo[i][j]:
			continue
		vlan_to_link[num] = (1+i, 1+j)
		link_to_vlan[(i+1, j+1)] = num
		num += 1
vlan_to_link[num] = (1, 0)
link_to_vlan[(1, 0)] = num
print("link to vlan:",link_to_vlan)
print("vlan to link:", vlan_to_link)
from utils.file_utils import save_pkl ,save_json
from path_utils import get_prj_root
import os 
save_pkl(os.path.join(get_prj_root(),"static/telemetry.link_to_vlan.pkl"),link_to_vlan)
save_pkl(os.path.join(get_prj_root(),"static/telemetry.vlan_to_link.pkl"),vlan_to_link)
save_json(os.path.join(get_prj_root(),"static/telemetry.vlan_to_link.json"),vlan_to_link)
# save_json(os.path.join(get_prj_root(),"static/telemetry.link_to_vlan.json"),link_to_vlan)
'''
# last_link=[]
# return_link=[]
# paths = load_json(os.path.join(get_prj_root(), "static/telemetry.paths.json"))["paths"]
# for path in paths:
# 	if (path[-1],path[-2]) not in return_link:
# 		return_link.append((path[-1],path[-2]))
# print(last_link)
'''