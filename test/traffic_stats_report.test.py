import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from utils.common_utils import is_digit, info, debug
from sockets.server import Server, recvall
import random
from itertools import islice


class PrintHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		data = str(recvall(self.request), "ascii")
		print(data)


if __name__ == '__main__':
	port = 1025
	server = Server(port, PrintHandler)
	server.start()
