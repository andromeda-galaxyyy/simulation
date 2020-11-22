import os
import threading
from typing import Callable

def kill_pid(pid:int):
	os.system("kill {}".format(pid))


def start_new_thread_and_run(func:Callable,args):
	threading.Thread(target=func,args=args).start()
