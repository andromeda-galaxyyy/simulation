import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from utils.common_utils import is_digit, info
from sockets.server import Server,recvall
import random


def check(content: str):
	try:
		obj = json.loads(content)
	except JSONDecodeError:
		return -1

	if "stats" not in list(obj.keys()):
		return -1
	stats = obj["stats"]
	if len(stats) != 8:
		return -1
	return stats


class DumbHandler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req_content = str(recvall(self.request), "utf-8")
		stats = check(req_content)
		if stats == -1:
			self.request.close()
			return
		obj = json.loads(req_content)
		info("received :{} ".format(obj))
		res = {"res": 0}
		r = random.random()
		if r >= 0.5:
			res["res"] += 1
		self.request.sendall(bytes(json.dumps(res), "utf-8"))


if __name__ == '__main__':
	server = Server(10000, DumbHandler)
	server.start()
