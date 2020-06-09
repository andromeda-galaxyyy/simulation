from datetime import datetime
import time


def now_in_milli():
	return int(round(time.time() * 1000))


def now_in_seconds():
	return now_in_milli() / 1000


def date():
	return str(datetime.now())
