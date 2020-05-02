import socket
import json
import sys
from sockets.server import recvall




if __name__ == '__main__':
	with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
		sock.connect(("localhost",10000))
		volumes=list(range(0,9*8*2))
		content={"volumes":volumes}
		sock.sendall(bytes(json.dumps(content),"utf-8"))
		resp=str(recvall(sock),"utf-8")
		print(resp)



