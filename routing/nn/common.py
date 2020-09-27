import os
from path_utils import get_prj_root
from utils.log_utils import debug,info,err

persist_dir = os.path.join(get_prj_root(), "routing", "nn","hdf5")
debug("Persist dir {}".format(persist_dir))