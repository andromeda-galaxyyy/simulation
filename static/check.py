from path_utils import get_prj_root
import os
from utils.file_utils import load_json, load_pkl
from utils.log_utils import debug, err, info

config = load_json(os.path.join(get_prj_root(), "static/military.config.json"))


def ping(ip: str):
	return os.system("ping -c 1 {}".format(ip))


all_workers_ip = set()
for _, ips in enumerate(config["workers_ip"]):
	for ip in ips:
		assert ip not in all_workers_ip
		all_workers_ip.add(ip)
		if 0 != ping(ip):
			err("Error when ping {}".format(ip))

debug(len(all_workers_ip))
