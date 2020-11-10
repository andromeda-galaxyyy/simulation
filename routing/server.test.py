import socket
import numpy as np
import json
from sockets.server import recvall2,recvall
from utils.time_utils import now_in_milli
from utils.log_utils import debug,info


if __name__ == '__main__':
	data=np.random.randint(100,1000,66*65*3).tolist()
	start=now_in_milli()
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.connect(("127.0.0.1", 1030))
		temp={
			"volumes":data
		}
		sock.sendall(bytes(json.dumps(temp)+"*", "ascii"))
		resp=recvall(sock)
		resp=resp.decode()
		debug("used {} milliseconds".format(now_in_milli()-start))
		resp=json.loads(resp)
		print(resp)
		debug(len(resp["res1"]))
		debug(len(resp["res2"]))
		debug(len(resp["res3"]))
		sock.shutdown(socket.SHUT_RDWR)
		sock.close()

