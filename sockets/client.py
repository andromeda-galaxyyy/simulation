import socket
import json
import sys
from typing import Dict
from utils.log_utils import debug
from sockets.server import recvall, recvall2


def send(ip: str, port: int, content: str):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.connect((ip, port))
		sock.sendall(bytes(content, "ascii"))
		sock.shutdown(socket.SHUT_RDWR)
		sock.close()


def send_and_recv(ip: str, port: int, content: str) -> str:
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
		sock.connect((ip, port))
		sock.sendall(bytes(content, "ascii"))
		resp = recvall2(sock)
		# debug(resp)
		sock.close()
		return resp


if __name__ == '__main__':
	x = [1 for _ in range(66 * 65)]
	obj={
		"topo_idx":0,
		"volumes":[],
	}

	for _ in range(3):
		obj["volumes"].extend(x)
	pre=None
	for idx in range(44):
		obj["topo_idx"]=idx
		resp=send_and_recv("192.168.1.132", 1055, json.dumps(obj) + "*")
		resp:Dict=json.loads(resp)
		assert pre!=resp
		assert "res1" in resp.keys()
		assert "res2" in resp.keys()
		assert "res3" in resp.keys()
		debug(resp)
		pre=resp
	
