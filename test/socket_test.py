import socket
import json
import sys

if __name__ == '__main__':
	with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
		sock.connect(("localhost",10000))
		content={"volumes":[1,2,3,4,5,6,7,8,9,10,11,12]}
		sock.sendall(bytes(json.dumps(content),"utf-8"))
		resp=str(sock.recv(2048),"utf-8")
		print(resp)



