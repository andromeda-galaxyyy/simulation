import socket
import json
import sys
from sockets.server import recvall
from time import sleep
import time



if __name__ == '__main__':
	for idx in range(44):
		with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
			sock.connect(("localhost",1028))
			req={"topo_idx":idx}
			sock.send(bytes(json.dumps(req),"ascii"))
			resp=str(recvall(sock),"ascii")
			obj=json.loads(resp)["res"]
			print(obj)
			assert len(obj)==66*65*2





