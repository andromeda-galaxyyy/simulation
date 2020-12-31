import os
import subprocess
import threading
from typing import Callable
from subprocess import DEVNULL, Popen
import shlex
from typing import Tuple


def kill_pid(pid: int):
	os.system("kill {}".format(pid))


def start_new_thread_and_run(func: Callable, args):
	threading.Thread(target=func, args=args).start()


def run_ns_process_background(ns: str, command, output=None) -> int:
	commands = "nohup ip netns exec {} {}".format(ns, command)
	out = DEVNULL if not output else open(output, "w")
	return subprocess.Popen(shlex.split(commands), stdout=out, stderr=out).pid


def run_process_background(command, output=None) -> int:
	out = DEVNULL if not output else open(output, "w")
	return subprocess.Popen(shlex.split(command), stdout=out, stderr=out).pid


def run_and_get_output(command) ->  str:
	ps = subprocess.Popen(command, stdout=subprocess.PIPE,shell=True)
	return ps.communicate()[0].decode("utf-8").strip()
	# return result.returncode, result.stdout.decode("utf-8")
