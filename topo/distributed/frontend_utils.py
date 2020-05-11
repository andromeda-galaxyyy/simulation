import os 
import time 
import datetime
import subprocess

def generate_host_ip(self, sw_id):
	sw_id = int(sw_id)
	assert sw_id < 253*253
	a = sw_id/253+1
	b = sw_id % 253+1
	return "10.0.{}.{}".format(a, b)


def attach_interface(s: str, port: str):
	os.system("ovs-vsctl add-port {} {}".format(s,port))


def detach_interface(s: str, port: str):
	os.system("ovs-vsctl del-port {} {}".format(s,port))


def del_interface(port: str):
	os.system("ip link del dev {}".format(port))


def down_interface(port: str):
	subprocess.run(["ifconfig",port,"down"])


def up_interface(port: str):
	subprocess.run(["ifconfig",port,"up"])


def del_tc(interface: str):
	os.system("tc qdisc del dev {} root netem".format(interface))


def add_tc(interface: str, delay, bandwidth):
	os.system("tc qdisc add dev {} root netem latency {} rate {}".format(interface, delay,bandwidth))

def now():
	return str(datetime.datetime.now())


class status:
	#error
	resource_not_found=-1
	rest_resource_not_found=404
	parameter_invalid=-2
	rest_parameter_invalid=401

	#ok
	operation_done=1
	rest_operation_done=200

