import socket
import json
import sys

if __name__ == '__main__':
	with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
		sock.connect(("localhost",10000))
		content={"stats":[1,2,3,4,5,6,7,8]}
		sock.sendall(bytes(json.dumps(content),"utf-8"))
		resp=str(sock.recv(2048),"utf-8")
		print(resp)



