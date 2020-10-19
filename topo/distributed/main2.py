import os

from argparse import ArgumentParser
from utils.file_utils import check_dir, check_file, load_json, load_pkl
from path_utils import get_prj_root
from utils.log_utils import debug, info, err
from utils.common_utils import is_digit
from topo.distributed.topo_scheduler import Scheduler2
from typing import Dict, List
import requests
import threading

tmp_dir = os.path.join(get_prj_root(), "topo/distributed/tmp")
iptables_bk = os.path.join(tmp_dir, "iptables.bk")
static_dir = os.path.join(get_prj_root(), "static")
topos_pkl = os.path.join(static_dir, "satellite_overall.pkl")


def do_post(url, obj):
	requests.post(url, json=obj)


def do_delete(url):
	requests.delete(url)


def cli(topos: List, config: Dict, scheduler: Scheduler2):
	traffic_started = False
	while True:
		try:
			print("> Available commands:\n"
			      "> 0.set up local switch\n"

			      "> 1.start topo scheduler\n"
			      "> 2.stop topo scheduler\n"

			      "> 3.start traffic (built in traffic generator,for test only)\n"
			      "> 4.stop traffic (built int traffic generator,for test only)\n"

			      "> 5.start traffic scheduler\n"
			      "> 6.stop traffic scheduler\n"

			      "> 7.quit\n"
			      "> 8.set up first topo\n"
			      "> 9.set up supplementary topo\n"
			      "> Press Enter to print this msg")

			command = input(">Input commands:\n").strip()
			if len(command) == 0:
				continue
			if not is_digit(command):
				# host = command.split(" ")[0]
				# commands = command.split(" ")[1:]
				# os.system("ip netns exec {}".format(command))
				continue

			command = int(command)

			if command == 0:
				intfs=config["workers_intf"]
				# set up local switch
				for idx, ip in enumerate(config["workers_ip"]):
					url = "http://{}:{}/config".format(ip, 5000)
					intf=intfs[idx]
					threading.Thread(target=do_post, args=[url, {"config": config, "id": idx,
					                                             "intf": intf}]).start()
				continue
			if command == 8:
				for idx, ip in enumerate(config["workers_ip"]):
					url = "http://{}:{}/topo".format(ip, 5000)
					threading.Thread(target=do_post, args=[url, {"topo": topos[0]["topo"]}]).start()
				continue

			if command == 1:
				debug("Topo scheduler started")
				scheduler.start()
				continue

			if command == 2:
				debug("Topo scheduler stoped")
				scheduler.stop()
				continue

			if command==5:
				for idx,ip in enumerate(config["workers_ip"]):
					url="http://{}:{}/traffic".format(ip,5000)
					threading.Thread(target=do_post,args=[url,{}]).start()
					continue

			if command==6:
				for idx,ip in enumerate(config["workers_ip"]):
					url="http://{}:{}/traffic".format(ip,5000)
					threading.Thread(target=do_delete,args=[url]).start()
					continue

			if command==7:
				scheduler.stop()
				for idx,ip in enumerate(config["workers_ip"]):
					url="http://{}:{}/config".format(ip,5000)
					threading.Thread(target=do_delete,args=[url]).start()
				continue
			if command==9:
				worker_ips=config["workers_ip"]
				#set up server access point
				url1 = "http://{}:{}/supplementary".format(worker_ips[0], 5000)
				threading.Thread(target=do_post,args=[url1,{"server":True}]).start()

				url2 = "http://{}:{}/supplementary".format(worker_ips[1], 5000)
				threading.Thread(target=do_post,args=[url2,{"server":False}]).start()
				continue

		except KeyboardInterrupt:
			print(">Preparing quit. Clean up")
			scheduler.stop()
			for idx,ip in enumerate(config["workers_ip"]):
				url="http://{}:{}/config".format(ip,5000)
				threading.Thread(target=do_delete,args=[url]).start()

			break


if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument("--config", type=str, help="config file name",
	                    default="/home/stack/code/simulation/topo/distributed/satellite.config.json")
	parser.add_argument("--topos_fn", type=str, help="Topo json file",
	                    default=topos_pkl)
	args=parser.parse_args()
	topos=load_pkl(args.topos_fn)
	config=load_json(args.config)
	scheduler=Scheduler2(config,topos)
	cli(topos,config,scheduler)


