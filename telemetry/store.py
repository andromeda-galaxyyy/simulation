import os
from utils.log_utils import debug, info
from typing import Dict, Tuple
from utils.time_utils import now_in_milli
import redis


class Store:
	def __init__(self, ip: str, port: int, db: int):
		self.handle = redis.Redis(host=ip, port=port, db=db)
		if self.handle.set("hello", "world"):
			info("Connect to redis {}:{} successfully".format(ip, port))

	def write_delay(self, link: Tuple[int, int], delay: float) -> bool:
		key = "{}-{}.delay".format(link[0], link[1])
		ts = now_in_milli()
		return 1 == self.handle.zadd(key, {
			delay: ts
		})

	def write_loss(self, link: Tuple[int, int], loss: float) -> bool:
		key = "{}-{}.loss".format(link[0], link[1])
		ts = now_in_milli()
		return 1 == self.handle.zadd(key, {
			loss: ts
		})

if __name__ == '__main__':
	store = Store("localhost", 6379, 7)
	import random
	from time import sleep
	for _ in range(10):
		sleep(0.5)
		assert store.write_delay((1, 2), random.random())
		assert store.write_loss((1, 2), random.random())
