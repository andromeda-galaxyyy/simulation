import os

from argparse import ArgumentParser
from pathlib import Path
import json
from topo.distributed.topobuilder import TopoBuilder
from path_utils import get_prj_root
from utils.file_utils import check_dir, check_file, load_json, load_pkl
from path_utils import get_prj_root
from utils.log_utils import debug, info, err
from utils.common_utils import is_digit
from typing import List
import netifaces
from topo.distributed.topo_scheduler import Scheduler
from utils.time_utils import run_at, roundTime
from topo.distributed.traffic_scheduler import TrafficScheduler
import datetime

tmp_dir = os.path.join(get_prj_root(), "topo/distributed/tmp")
iptables_bk = os.path.join(tmp_dir, "iptables.bk")
static_dir = os.path.join(get_prj_root(), "static")
topos_pkl = os.path.join(static_dir, "satellite_overall.pkl")


def cli(manager: TopoBuilder, scheduler: Scheduler):
	traffic_started = False
	while True:
		try:
			print(">Available commands:\n"
			      ">0.start scheduler\n"
			      ">1.start traffic (built in traffic generator,for test only)\n"
			      ">2.stop traffic (built int traffic generator,for test only)\n"
			      ">3.start traffic scheduler\n"
			      ">4.stop traffic scheduler\n"
			      ">5.quit\n"
			      ">6.stop topo scheduler\n"
			      ">Or any command which will be run in some namespace\n")
			command = input(">Input commands:\n").strip()
			if len(command)==0:
				continue
			if not is_digit(command):
				host = command.split(" ")[0]
				commands = command.split(" ")[1:]
				os.system("ip netns exec {}".format(command))
				# todo support namespace command
				continue

			command = int(command)

			if command == 0:
				t = roundTime()
				t += datetime.timedelta(0, 60, 0)
				info("Topo scheduler will run at {}".format(t))
				run_at(t, scheduler.start)

			if command == 1:
				if not traffic_started:
					print(">Starting ")
					manager.start_gen_traffic()
					traffic_started = True
				else:
					print(">Traffic generator already started")
					continue
				continue
			if command == 2:
				manager.stop_traffic()
				traffic_started = False
				continue
			if command==3:
				manager.start_gen_traffic_use_scheduler()
				continue
			if command==4:
				manager.stop_traffic_use_scheduler()
				continue

			if command == 5:
				print(">Preparing quit. Clean up")
				scheduler.stop()
				manager.stop()
				break

		except KeyboardInterrupt:
			print(">Preparing quit. Clean up")
			scheduler.stop()
			manager.stop()
			break


if __name__ == '__main__':

	parser = ArgumentParser()
	parser.add_argument("--config", type=str, help="config file name",
	                    default="/home/stack/code/simulation/topo/distributed/satellite.config.json")
	parser.add_argument("--intf", type=str, help="interface to access network", default="eno1")
	# parser.add_argument("--topo", type=str, help="Topo json file",
	#                     default="/home/stack/code/simulation/topo/distributed/satellite.json")
	parser.add_argument("--topos", type=str, help="Topo json file",
	                    default=topos_pkl)
	parser.add_argument("--id", required=True, type=str, help="Worker id")
	args = parser.parse_args()

	config_fn = args.config
	topo_fn = args.topos
	# check file
	check_file(config_fn)
	config = load_json(config_fn)
	# check config
	check_file(config["traffic_generator"])
	# check_file(config["listener"])
	check_dir(config["traffic_dir"]["default"])

	check_file(topo_fn)
	topos = load_pkl(topo_fn)
	assert len(topos) == 44

	# back up iptables
	os.system("iptables-save > {}".format(iptables_bk))
	worker_id = int(args.id)
	info("Worker id:{}".format(worker_id))
	# check intf
	intf = args.intf
	if intf not in netifaces.interfaces():
		err("Cannot find interfaces {}".format(intf))
		exit(-1)

	builder = TopoBuilder(load_json(config_fn), worker_id, args.intf)
	scheduler = Scheduler(worker_id, config, topos, builder)

	builder.diff_topo(topos[0]["topo"])
	info("Topo set")
	cli(builder, scheduler)
