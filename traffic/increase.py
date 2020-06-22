import os 

from pathlib import Path
import shutil

idx=0

for file in os.listdir("/tmp/pkts/voip"):
    if ".pkts" not in file:continue 
    for _ in range(60):
        shutil.copyfile(os.path.join("/tmp/pkts/voip",file),os.path.join("/tmp/pkts/voip","{}.pkts".format(idx)))
        idx+=1
    