import socket

import sys
import json
import threading
import socketserver
from utils.common_utils import is_digit
from multiprocessing import Pool

socketserver.TCPServer.allow_reuse_address = True

BUFF_SIZE = 4096  # 4 KiB


def recvall(req):
	data = b''
	while True:
		part = req.recv(BUFF_SIZE)
		if not part:
			break
		data += part
	return data


def recvall2(sock: socket):
	data = b''
	while True:
		part = sock.recv(BUFF_SIZE)
		if len(part) == 0:
			continue
		piece = part.decode()
		data += part
		# print(data)
		if len(piece) > 0 and piece[-1] == '*':
			break

	if len(data) == 0:
		return ""
	else:
		res = data.decode()
		return res[:-1]


def sendall(sock: socket, msg: str):
	sock.sendall(bytes(msg + "*", "ascii"))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
	pass


class Server:
	def __init__(self, port, handler):
		assert is_digit(port)
		self.port = int(port)
		self.started = False
		self.handler = handler

	def start(self):
		# server=ThreadedTCPServer(("0.0.0.0",self.port),self.handler)
		server = socketserver.ThreadingTCPServer(("0.0.0.0", self.port), self.handler)
		server.serve_forever()


# with server:
# 	# ip,port=server.server_address
# 	server_thread=threading.Thread(target=server.serve_forever)
# 	server_thread.daemon=True
# 	server_thread.start()
# 	server.serve_forever()
# server.shutdown()


class Handler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		data = str(self.request.recv(2048), "utf-8")
		cur_thread = threading.current_thread()
		response = "echo {} from {}".format(data, cur_thread)
		response = bytes(response, "utf-8")
		self.request.sendall(response)


if __name__ == '__main__':
	port = 9999
	server = Server(9999, Handler)
	server.start()
