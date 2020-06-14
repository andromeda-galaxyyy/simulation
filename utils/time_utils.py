import datetime
import time
import threading


def now_in_milli():
	return int(round(time.time() * 1000))


def now_in_seconds():
	return now_in_milli() / 1000


def date():
	return str(datetime.datetime.now())


def roundTime(dt=None, roundTo=60):
	'''
	获取将来最近的时间，以分钟记
	:param dt:
	:param roundTo:
	:return:
	'''

	if dt is None:
		dt = datetime.datetime.now()
	seconds = (dt.replace(tzinfo=None) - dt.min).seconds
	rounding = (seconds + roundTo / 2) // roundTo * roundTo
	return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)


def run_at(t, f, *args, **kwargs):
	now = datetime.datetime.now()
	delay = (t - now).total_seconds()
	threading.Timer(delay, f, args, kwargs).start()


def roundTime2(dt=None, dateDelta=datetime.timedelta(minutes=1)):
	"""Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
            Stijn Nevens 2014 - Changed to use only datetime objects as variables
    """
	roundTo = dateDelta.total_seconds()

	if dt == None: dt = datetime.datetime.now()
	seconds = (dt - dt.min).seconds
	# // is a floor division, not a comment on following line:
	rounding = (seconds + roundTo / 2) // roundTo * roundTo
	return dt + datetime.timedelta(0, rounding - seconds, -dt.microsecond)


if __name__ == '__main__':
	def print_str(s):
		print(s)

	print("time round up to {}".format(roundTime2()+datetime.timedelta(0,60,0)))


