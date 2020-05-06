import socket
import sys
import json
from json import JSONDecodeError
import threading
import socketserver
from utils.common_utils import is_digit, info
from sockets.server import Server,recvall
from classify.model import Dumb
import random
import numpy as np

dumb_classifier=Dumb()

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
		req_content = str(recvall(self.request), "ascii")
		stats = check(req_content)
		if stats == -1:
			self.request.close()
			return
		obj = json.loads(req_content)
		info("received :{} ".format(obj))
		res= {"res": dumb_classifier.predict(np.asarray(stats))}
		self.request.sendall(bytes(json.dumps(res), "ascii"))


if __name__ == '__main__':
	server = Server(10000, DumbHandler)
	server.start()
