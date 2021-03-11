from utils.log_utils import debug, info, err
from utils.file_utils import read_lines
from typing import Tuple, Dict, List
import os
import argparse


def parse_file(fn: str):
	lines = read_lines(fn)
	traffic = []
	for l in lines:
		contents = l.strip().split(" ")
		traffic.append([contents[0], contents[1], float(contents[2])])
	traffic.sort(key=lambda x: x[2], reverse=True)
	for t in traffic[:20]:
		print("src {},dst {},traffic {}".format(t[0], t[1], t[2]))


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--fn", type=str)
	args = parser.parse_args()
	fn = os.path.join("/tmp/data", args.fn)
	parse_file(fn)
