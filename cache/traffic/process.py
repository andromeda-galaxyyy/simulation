from utils.file_utils import *
from utils.log_utils import *
import json
from path_utils import get_prj_root
import os
from routing.instance import ILPInput
from itertools import product

traffic_dir=os.path.join(get_prj_root(),"cache/traffic")
files={
	"video":os.path.join(traffic_dir,"video.traffic.txt"),
	"iot":os.path.join(traffic_dir,"iot.traffic.txt"),
	"voip":os.path.join(traffic_dir,"voip.traffic.txt")
}

traffic={
	"video":[],
	"iot":[],
	"voip":[],
}

res=[]

for traffic_type,fn in files.items():
	count=0
	with open(fn,"r") as fp:
		lines=fp.readlines()
		lines=[l[l.index("{"):] for l in lines]
		for l in lines:
			obj=json.loads(l)
			if int(obj["average1"])+int(obj["average2"])+int(obj["average3"])<1000:
				continue

			stats=obj["volumes"]
			# stat=[0 for _ in range(66*65)]
			for idx in range(66*65):
				stats[idx]+=stats[idx+66*65]
				stats[idx]+=stats[idx+66*65*2]
			traffic[traffic_type].append(stats[:66*65])
			count+=1
	debug("{} traffic {}".format(traffic_type,count))


debug("sorted start")
traffic["video"].sort(key=lambda x:len([y for y in x if y>10]),reverse=True)
traffic["iot"].sort(key=lambda x:len([y for y in x if y>10]),reverse=True)
traffic["voip"].sort(key=lambda x :len([y for y in x if y>10]),reverse=True)
debug("sorted done")

num=50

res=[
	ILPInput(video=a,iot=b,voip=c,ar=d) for a in traffic["video"][:num] for b in traffic["iot"][:num] for c in traffic["voip"][:num] for d in traffic["video"][:num]
]


res_fn=os.path.join(traffic_dir,"ilp_inputs.pkl")
debug("start to save")
save_pkl(res_fn,res)
debug("save done")









