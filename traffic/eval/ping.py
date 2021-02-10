from utils.log_utils import debug,info,err
from utils.file_utils import del_dir,create_dir,dir_exsit
import os
from utils.process_utils import run_ns_process_background

outdir="/tmp/pingdelay20"

def run_pingparse():
    for _ in range(100):
        fn=os.path.join(outdir,"ping.{}.json".format(_))
        command="pingparsing -c 100 10.0.0.4 --quiet > {}".format(fn)
        os.system(command)
        # run_ns_process_background("h0",command,fn)



if __name__ == '__main__':
    if not dir_exsit(outdir):
        create_dir(outdir)
    run_pingparse()
