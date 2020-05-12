import socket
import json
import sys
from sockets.server import recvall
from time import sleep
import time



if __name__ == '__main__':
	while True:
		with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
			sock.connect(("localhost",1025))
			obj="{\"stats\":[15.88976642985235, 18.461668908702073, 10.919648905800928, 14.159993568835397, 19.103208307744154, 12.624529936756492, 17.360818844845653, 16.32638567869324]}"

			sock.sendall(bytes(obj,"ascii"))
			resp=str(recvall(sock),"ascii")


			millis = int(round(time.time() * 1000))

			print("received ",resp," ",millis)
			sleep(0.001)




