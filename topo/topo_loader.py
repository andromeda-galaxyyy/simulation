import matplotlib
from numpy.lib.npyio import _save_dispatcher

matplotlib.use('agg')
import numpy as np
from utils.common_utils import load_pkl, save_pkl, save_json, is_digit, check_file, check_dir, \
	file_exsit, dir_exsit
import matplotlib.pyplot as plt
import networkx as nx
from itertools import islice
import pathlib
import random
from collections import Counter
from typing import List, Tuple, Dict, DefaultDict
import cplex
from utils.common_utils import debug, info, err
from utils.num_utils import gaussion, uniform
import os
from path_utils import get_prj_root
from copy import deepcopy
from argparse import ArgumentParser
from common.graph import NetworkTopo
# import tmgen
# from tmgen.models import random_gravity_tm
import random

cache_dir = os.path.join(get_prj_root(), "cache")
satellite_topo_dir = os.path.join(get_prj_root(), "routing/satellite_topos")
static_dir = os.path.join(get_prj_root(), "static")


def is_connected(topo, i, j):
	if not is_digit(topo[i][j]):
		return False
	return float(topo[i][j]) > 0


def link_switch_cost(inter: float):
	return 10 / np.exp(inter / 100)


def read_statellite_topo():
	satellite_topos = []
	fn = os.path.join(satellite_topo_dir, "delaygraph_py3_v2.txt")
	old_topos = load_pkl(fn)
	intervals = []
	for _ in range(22):
		intervals.append(157)
		intervals.append(116)
	epoch_time = sum(intervals)
	long_lasting_edge = set()
	exits_intervals = []
	new_topos = []

	for old_topo_idx, old_topo in enumerate(old_topos):
		links = set()
		nodes = len(old_topo)
		new_topo = [[[-1, -1, -1, -1] for _ in range(nodes)] for _ in range(nodes)]

		for i in range(nodes):
			for j in range(i + 1, nodes):
				if not is_connected(old_topo, i, j):
					continue
				links.add((i, j))
				# capacity = uniform(4000, 7000)
				capacity = 100
				delay = float(old_topo[i][j])
				delay *= 1000
				delay = int(delay)

				# 容量，延迟、loss,switch_cost
				spec = [capacity, delay, 0, 0]
				next_iterval = 0
				idx2 = old_topo_idx
				always_connected = False
				count_interval = 0
				while True:
					count_interval += 1
					next_iterval += intervals[idx2]
					idx2 = (idx2 + 1) % len(old_topos)
					next_old_topo = old_topos[idx2]

					if not is_connected(next_old_topo, i, j):
						exits_intervals.append(count_interval)
						break
					if next_iterval > epoch_time:
						long_lasting_edge.add((i, j))
						always_connected = True
						break
				if always_connected:
					spec[-1] = 0
				else:
					spec[-1] = float(link_switch_cost(next_iterval))
				# print(spec[2])
				new_topo[i][j] = deepcopy(spec)
				new_topo[j][i] = deepcopy(spec)
		# print(len(links))
		new_topos.append(deepcopy(new_topo))
		satellite_topos.append({
			"topo": new_topo,
			"duration": intervals[old_topo_idx]
		})
	assert len(satellite_topos) == 44

	topo_fn = os.path.join(cache_dir, "topo.pkl")

	save_pkl(topo_fn, new_topos)
	save_pkl(os.path.join(static_dir, "satellite_overall.pkl"), satellite_topos)
	debug("satellite topo saved")


read_statellite_topo()


# read millitary project topo

def convert_satellite_topo(topo: List[List[List[int]]]) -> List[List[List[int]]]:
	link: List[int] = [100, 10, 0, 0]
	new_topo: List[List[List[int]]] = [[[-1, -1, -1, -1]
	                                    for _ in range(100)] for _ in range(100)]

	# print(new_topo[0][0])

	def connect(s1, s2):
		new_topo[s1][s2] = link
		new_topo[s2][s1] = link

	for i in range(66):
		for j in range(66):
			new_topo[i][j] = topo[i][j]

	# node=0
	# for idx in range(66,66+17):
	# 	connect(idx,node)
	# 	node+=1

	node_id = 65
	for idx in range(6):
		node_id += 1
		connect(node_id, 2 + idx * 11)
		connect(node_id, 3 + idx * 11)
		node_id += 1
		connect(node_id, 2 + idx * 11)
		connect(node_id, 3 + idx * 11)
		node_id += 1
		connect(node_id, 8 + idx * 11)
		connect(node_id, 9 + idx * 11)
		node_id += 1
		connect(node_id, 8 + idx * 11)
		connect(node_id, 9 + idx * 11)
		# node=70
		node_id += 1
		connect(node_id, node_id - 1)
		connect(node_id, node_id - 4)

		if idx <= 3:
			# node=71
			node_id += 1
			connect(node_id, node_id - 4)
			connect(node_id, node_id - 3)

	# assert node == 99
	# check
	# count=0
	# for i in range(100):
	# 	for j in range(100):
	# 		if new_topo[i][j]!=[-1,-1,-1,-1]:
	# 			count+=1
	return new_topo


def load_military_topo():
	satellites = load_pkl(os.path.join(static_dir, "satellite_overall.pkl"))
	millitary = []
	for idx, topo in enumerate(satellites):
		new_topo=convert_satellite_topo(topo["topo"])
		if idx==0:
			tmp=[[0 for _ in range(100)]for _ in range(100)]
			for i in range(100):
				for j in range(100):
					if -1 not in new_topo[i][j]:
						tmp[i][j]=1
			save_json("/tmp/topo.json",{"topo":tmp})
		millitary.append({
			"topo": new_topo,
			"duration": topo["duration"]
		})

	debug("military topo converted")
	save_pkl(os.path.join(static_dir, "military.pkl"), millitary)


load_military_topo()
