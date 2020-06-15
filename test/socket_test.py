import socket
import json
import sys
from sockets.server import recvall,recvall2,sendall
from time import sleep
import time



if __name__ == '__main__':
	for idx in range(44):
		with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
			sock.connect(("192.168.1.90",1028))
			req={"topo_idx":idx}
			sendall(sock,json.dumps(req))
			resp=recvall2(sock)
			print(resp)
			obj=json.loads(resp)["res"]
			assert len(obj)==66*65*2





