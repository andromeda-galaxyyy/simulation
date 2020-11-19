import os

def kill_pid(pid:int):
	os.system("kill {}".format(pid))
