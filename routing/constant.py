import os
from path_utils import get_prj_root
from utils.log_utils import debug,info,err

persist_dir = os.path.join(get_prj_root(), "routing", "nn", "nn/hdf5")
debug("Persist dir {}".format(persist_dir))


instances_dir=os.path.join(get_prj_root(),"routing","instances")
n_nodes=66
n_ksp=3
n_flows=4


batch_size=64

topo_fn=os.path.join(get_prj_root(),"cache","topo.pkl")


