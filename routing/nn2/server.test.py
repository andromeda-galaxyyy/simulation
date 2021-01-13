from utils.log_utils import info,err,debug
from sockets.client import send_and_recv
from utils.file_utils import load_json,save_json
from path_utils import get_prj_root
from utils.file_utils import static_dir
import json
import os

topo_fn=os.path.join(get_prj_root(),"static/topo.json")
topo=load_json(topo_fn)["topo"]


if __name__ == '__main__':
    req={}
    for i in range(100):
        for j in range(100):
            if i==j:continue
            if i>j:continue
            if -1 in topo[i][j]:continue
            key="{}-{}".format(i,j)
            req[key]=100

    resp=send_and_recv("localhost",7788,json.dumps(req)+"*")
    paths=json.loads(resp)["res1"]
    debug("**** {}".format(len(paths)))
    idx=0
    for i in range(100):
        for j in range(100):
            if i==j:continue
            path=paths[idx]
            idx+=1
            assert path[0]==i
            assert path[-1]==j
            if i==0 and j==1 :debug(path)



