from pathlib import Path
import json
import pickle
import os
import shutil
from typing import Callable, List, Dict, Tuple
import os


def check_dir(dir_name):
	if not Path(dir_name).is_dir():
		raise FileNotFoundError


def check_file(fn):
	if not Path(fn).is_file():
		raise FileNotFoundError


def file_exsit(fn):
	return Path(fn).is_file()


def read_lines(fn: str) -> List[str]:
	res = None
	if not file_exsit(fn):
		return []
	with open(fn, "r") as fp:
		res = fp.readlines()
		res = [r for r in res if len(r.strip()) != 0]
	return res


def read_lines_with_action(fn: str,action:Callable) -> List:
	res = []
	if not file_exsit(fn):
		return []
	with open(fn, "r") as fp:
		while True:
			line=fp.readline()
			line=line.strip()
			if len(line)==0:break
			converted=action(line)
			if line is not None:
				res.append(converted)
	return res

def dir_exsit(fn):
	return Path(fn).is_dir()


def create_dir(dirname):
	os.mkdir(dirname)


def del_dir(dirname):
	shutil.rmtree(dirname, ignore_errors=True)


def load_pkl(filename):
	if Path(filename).is_file():
		data = None
		with open(filename, 'rb') as file:
			data = pickle.load(file)
			file.close()
			return data
	raise FileNotFoundError


def save_pkl(filename, obj, overwrite=True):
	def write():
		with open(filename, 'wb') as file:
			pickle.dump(obj, file)
			file.flush()
			file.close()

	if Path(filename).is_file() and overwrite:
		write()
		return

	write()


def load_json(filename):
	if Path(filename).is_file():
		with open(filename) as f:
			return json.load(f)
	raise FileNotFoundError


def save_json(filename, obj, overwrite=True):
	def write():
		with open(filename, 'w', encoding="utf8") as file:
			json.dump(obj, file, indent=4)

	if Path(filename).is_file and overwrite:
		write()
		return
	write()


def walk_dir(d: str, filter_func: Callable[[str], bool]) -> List[str]:
	res = []
	for path, subdirs, files in os.walk(d):
		for name in files:
			if not filter_func(name): continue
			res.append(os.path.join(path, name))

	return res


def write_to_file(content, fn: str):
	if file_exsit(fn):
		os.remove(fn)
	with open(fn, "w") as fp:
		fp.write("{}".format(content))
		fp.flush()


# def write_to_file(content,fn:str):
#     if
#     with open(content)


import os
from path_utils import get_prj_root

static_dir = os.path.join(get_prj_root(), "static")
