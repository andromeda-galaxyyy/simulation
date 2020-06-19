import socket
import json
import sys
from sockets.server import recvall,recvall2,sendall
from time import sleep
import time


if __name__ == '__main__':
	# for idx in range(44):
	with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
		sock.connect(("localhost",1026))
		req={"specifier":["" for _ in range(5)],"stats":[1 for _ in range(8)]}
		sendall(sock,json.dumps(req))
		resp=recvall(sock)
		print(resp)
		# obj=json.loads(resp)["res"]
		# assert len(obj)==66*65*2





