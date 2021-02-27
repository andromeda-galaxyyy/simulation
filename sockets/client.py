import socket
import json
import sys
from typing import Dict
from utils.log_utils import debug
from sockets.server import recvall, recvall2
from utils.file_utils import save_json
from routing.nn3.contants import flattenidxes


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
	req={
		"matrix":{
			"0":[0 for _ in range(100*99)],
			"1": [0 for _ in range(100 * 99)],
			"2": [0 for _ in range(100 * 99)],
			"3": [0 for _ in range(100 * 99)],
		}
	}
	resp=send_and_recv("192.168.1.196",1055,json.dumps(req)+"*")
	resp=json.loads(resp)
	debug(len(resp["res1"]))
	routing=resp["res1"]
	debug(routing[flattenidxes[(10,99)]])

	# tmp=[0 for _ in range(100*99)]
	# req={
	# 	"0":tmp,
	# 	"1":tmp,
	# 	"2":tmp,
	# 	"3":tmp
	# }
	# resp=send_and_recv("192.168.1.196",1053,"default*")
	# save_json("/tmp/military.default_routing.json",resp)
	# debug(resp)

	# x = [1 for _ in range(66 * 65)]
	# obj={
	# 	"topo_idx":0,
	# 	"volumes":[],
	# }
	#
	# for _ in range(3):
	# 	obj["volumes"].extend(x)
	# pre=None
	# for idx in range(44):
	# 	obj["topo_idx"]=idx
	# 	resp=send_and_recv("192.168.1.132", 1055, json.dumps(obj) + "*")
	# 	resp:Dict=json.loads(resp)
	# 	assert pre!=resp
	# 	assert "res1" in resp.keys()
	# 	assert "res2" in resp.keys()
	# 	assert "res3" in resp.keys()
	# 	debug(resp)
	# 	pre=resp
	
