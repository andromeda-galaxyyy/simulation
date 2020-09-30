from routing.nn.minor import Minor
from utils.file_utils import *
from utils.log_utils import debug, info, err
from argparse import ArgumentParser
from multiprocessing import Process
from typing import List, Dict, Tuple, Any
import numpy as np
from routing.instance import RoutingInput, RoutingOutput, ILPInput, ILPInstance, ILPOutput
from routing.instance import RoutingInstance, map_instance
from sklearn.preprocessing import MinMaxScaler
from path_utils import get_prj_root
import random
from routing.nn.dataset_generator import ILPGenerator, get_ilp_generator

# 多进程使用gpu
# https://docs.nvidia.com/deploy/mps/index.html

# parse

'''
dataset中每个instance
N=66
[(流量矩阵,路径选择)]
流量矩阵 流量种类*N*(N-1)
路径选择 流量种类*N*(N-1)
'''


def load_ilp_dataset(fn: str) -> List[RoutingInstance]:
	instances = []
	for path, subdirs, files in os.walk(fn):
		for file in files:
			if "ilpinstance" not in file: continue
			instances.extend(load_pkl(os.path.join(fn, file)))
	return instances


def train_runner(ids: List[int], n_flows: int, n_nodes: int, n_ksp: int,
                 dataset: List[RoutingInstance],
                 ratio=0.7, shuffle=False):
	def mapper(instance: RoutingInstance) -> Tuple[List, List]:
		traffic_matrix = []
		labels = []
		traffic_matrix.extend(instance.video)
		labels.extend(instance.labels["video"])
		traffic_matrix.extend(instance.iot)
		labels.extend(instance.labels["iot"])
		traffic_matrix.extend(instance.voip)
		labels.extend(instance.labels["voip"])
		traffic_matrix.extend(instance.ar)
		labels.extend(instance.labels["ar"])

		return traffic_matrix, labels

	# return res, labels

	# train  (matrix,labels)
	train, test = map_instance(dataset, mapper, ratio, shuffle)
	train_x = np.asarray([t[0] for t in train])
	train_y = np.asarray([t[1] for t in train])

	test_x = np.asarray([t[0] for t in test])
	test_y = np.asarray([t[1] for t in test])

	for id_ in ids:
		# (instance,4,65*66)
		train_y = np.reshape(train_y, (-1, n_flows, (n_nodes - 1) * n_nodes))
		test_y = np.reshape(test_y, (-1, n_flows, (n_nodes - 1) * n_nodes))

		y = train_y[:, :, id_ * (n_nodes - 1):(id_ + 1) * (n_nodes - 1)]
		yy = test_y[:, :, id_ * (n_nodes - 1):(id_ + 1) * (n_nodes - 1)]
		# y = np.reshape(y, (-1, n_flows, n_nodes - 1))

		# yy = test_y[:, id_ * n_flows * (n_nodes - 1):(id_ + 1) * n_flows * (n_nodes - 1)]
		# yy = np.reshape(yy, (-1, n_flows, n_nodes - 1))

		model = Minor(id_, n_nodes, n_flows, n_ksp)
		# model.load_model()
		model.build()

		model.fit((train_x, y), (test_x, yy))


# # # 统计非0正确性
# count = 0
# #
# random_idx = np.random.randint(0, len(test))
# xxx = test_x[random_idx]
#
# tmp_x = np.reshape(xxx, (-1, 66 * 65, 4))
# tmp_x = np.reshape(tmp_x[:,id_ * 65:(id_ + 1) * 65, :], (-1, 65 * 4))[0][:65]
# none_zero = len([y for y in tmp_x if y > 0])
#
# print(none_zero)
#
# xxx = np.asarray([xxx])
# yyy = test_y[random_idx]
# yyy = yyy[id_ * n_flows * (n_nodes - 1):(id_ + 1) * n_flows * (n_nodes - 1)]
# # yyy = np.asarray(yyy)
#
# actions = model.predict(xxx)[0]
# actions = np.reshape(actions, (-1, n_flows * (n_nodes - 1)))[0]
#
# for idx in range(len(actions)):
# 	if idx>65:continue
# 	if actions[idx] == yyy[idx]:
# 		count += 1
#
# print(count / none_zero)


default_instance_dir = os.path.join(get_prj_root(), "routing", "instances")


def train_with_generator(ids=None,
                         instance_dir: str = default_instance_dir,
                         n_nodes: int = 66,
                         n_flows: int = 4,
                         n_ksp: int = 3,
                         ratio=0.7,
                         ):
	if ids is None:
		ids = list(range(66))
	files = []
	for file in os.listdir(instance_dir):
		if "ilpinstance" not in file: continue
		files.append(os.path.join(instance_dir, file))
	# for path, subdidrs, files in os.walk(instance_dir):
	# 	for file in files:
	# 		if "ilpinstance" not in file: continue
	# 		files.append(os.path.join(instance_dir, file))

	info("scan file done files {}".format(len(files)))
	n_train_files = int(len(files) * ratio)
	n_test_files = len(files) - n_train_files
	train_files = files[:n_train_files]
	test_files = files[n_train_files:]
	info("#train files {}".format(n_train_files))
	info("#test files {}".format(n_test_files))

	for model_id in ids:
		train_generator = ILPGenerator(train_files, model_id, n_nodes=n_nodes, n_ksp=n_ksp,
		                               n_flows=n_flows, batch_size=32)
		validate_generator = ILPGenerator(test_files, model_id, n_nodes=n_nodes, n_ksp=n_ksp,
		                                  n_flows=n_flows, batch_size=32)
		model = Minor(model_id, n_nodes, n_flows, n_ksp)
		model.build()
		info("Model {} start to fit".format(model_id))
		model.fit_with_generator(train_generator, validate_generator)
		info("Model {} trained".format(model_id))


def train_with_dataset(ids=None,
                       instance_dir: str = default_instance_dir,
                       n_nodes: int = 66,
                       n_flows: int = 4,
                       n_ksp: int = 3,
                       ratio=0.8,
                       ):
	info("train with ids {}".format(ids))

	if ids is None:
		ids = list(range(66))
	fns = []
	for path,subdirs,files in os.walk(instance_dir):
		for name in files:
			if "ilpinstance" not in name: continue
			fns.append(os.path.join(path,name))

	info("scan file done files {}".format(len(fns)))
	n_train_files = int(len(fns) * ratio)
	n_test_files = len(fns) - n_train_files
	train_files = fns[:n_train_files]
	validate_files = fns[n_train_files:]
	info("#train files {}".format(n_train_files))
	info("#test files {}".format(n_test_files))

	for model_id in ids:
		train_dataset = get_ilp_generator(train_files, model_id)
		validate_dataset = get_ilp_generator(validate_files, model_id)
		model = Minor(model_id, n_nodes, n_flows, n_ksp)
		model.build()
		info("Model {} start to fit".format(model_id))
		model.fit_with_dataset(train_dataset, validate_dataset)
		info("Model {} trained".format(model_id))


def main():
	n_nodes = 66

	instance_dir = os.path.join(get_prj_root(), "routing", "instances")

	parser = ArgumentParser()
	parser.add_argument("--workers", type=int, default=3)
	parser.add_argument("--id", type=int, default=0)
	# parser.add_argument("--gpu",type=int,default=0)
	args = parser.parse_args()

	# read ids and runner
	worker_id = int(args.id)
	n_workers = int(args.workers)
	tasks_per_worker = n_nodes // n_workers

	ids = list(range(n_nodes))[worker_id * tasks_per_worker:(worker_id + 1) * tasks_per_worker]
	train_with_dataset(ids)


def test_train_runner():
	ids = [24]
	instances = []
	instance_dir = os.path.join(get_prj_root(), "routing", "instances")
	for file in os.listdir(instance_dir):
		if "ilpinstance" not in file: continue
		instances.extend(load_pkl(os.path.join(instance_dir, file)))

	info("ILPInstances: {}".format(len(instances)))
	n_instance = len(instances)
	random.shuffle(instances)

	train_runner(ids, 4, 66, 3, instances[:n_instance])


if __name__ == '__main__':
	main()
#
# n_nodes = 66
#
# instance_dir = os.path.join(get_prj_root(), "routing", "instances")
# parser = ArgumentParser()
# parser.add_argument("--workers", type=int, default=3)
# parser.add_argument("--id", type=int, default=0)
# parser.add_argument("--gpu",type=int,default=0)
# args = parser.parse_args()
# os.environ["CUDA_VISIBLE_DEVICES"]="1"
# all_ids=list(range(n_nodes))
# n_ids_per_worker=
# train_with_dataset([24])
