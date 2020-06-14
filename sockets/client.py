import socket
import json
import sys

from sockets.server import recvall

def send(ip:str,port:int,content:str):
	with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
		sock.connect((ip,port))
		sock.sendall(bytes(content,"ascii"))
		resp=str(recvall(sock),"ascii")
		sock.close()
