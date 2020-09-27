from routing.models.minor import Minor
from utils.file_utils import *
from utils.log_utils import debug, info, err
from argparse import ArgumentParser
from multiprocessing import Process
from typing import List, Dict, Tuple, Any
import numpy as np
from routing.instance import ILPInput
from routing.instance import ILPInstance, map_instance
from sklearn.preprocessing import MinMaxScaler


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


def load_ilp_dataset(fn: str) -> List[ILPInstance]:
	dataset = load_pkl(fn)
	return dataset


def train_runner(ids: List[int], n_flows: int, n_nodes: int, n_ksp: int, dataset: List[ILPInstance],
                 ratio=0.7, shuffle=False):
	def mapper(instance: ILPInstance) -> Tuple[List, List]:
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

		return traffic_matrix,labels
		# return res, labels

	# train  (matrix,labels)
	train, test = map_instance(dataset, mapper, ratio, shuffle)
	train_x = np.asarray([t[0] for t in train])
	train_y = np.asarray([t[1] for t in train])

	test_x = np.asarray([t[0] for t in test])
	test_y = np.asarray([t[1] for t in test])

	for id_ in ids:
		assert len(train_x[0]) == n_flows * n_nodes * (n_nodes - 1)
		y = train_y[:, id_ * n_flows * (n_nodes - 1):(id_ + 1) * n_flows * (n_nodes - 1)]
		assert len(y[0]) == n_flows * (n_nodes - 1)
		y = np.reshape(y, (-1, n_flows, n_nodes - 1))

		yy = test_y[:, id_ * n_flows * (n_nodes - 1):(id_ + 1) * n_flows * (n_nodes - 1)]
		yy = np.reshape(yy, (-1, n_flows, n_nodes - 1))

		model = Minor(id_, n_nodes, n_flows, n_ksp)
		model.build()
		model.fit((train_x, y), (test_x, yy))


def predict_runner(ids: List[int], n_flows: int, n_nodes: int, n_ksp: int, dataset: List[Tuple]):
	# model=Minor(id_,n_nodes,n_flows,n_ksp)
	# model
	pass


def main():
	n_nodes = 66
	max_jobs_per_worker = 10
	dataset_fn = ""
	parser = ArgumentParser()
	default_ids = ",".join(list(range(n_nodes)))
	# "0,1,2,3,4,5"
	parser.add_argument("--ids", type=str, default=default_ids)
	args = parser.parse_args()
	dataset = load_ilp_dataset(dataset_fn)
	processes = []

	# read ids and runner
	ids = list(map(int, args.ids.split(",")))

	# start new process
	num_process = 1 + len(ids) // max_jobs_per_worker
	for idx in range(num_process):
		if idx != num_process - 1:
			sub_ids = ids[idx * max_jobs_per_worker:(idx + 1) * max_jobs_per_worker]
		else:
			sub_ids = ids[idx * max_jobs_per_worker:]
		p = Process(target=train_runner, args=(sub_ids, dataset))
		p.start()
		processes.append(p)

	for p in processes:
		p.join()


def test_train_runner():
	ids = [1]
	fn = "/tmp/ilpinstance.0.partition.2.pkl"
	instances = load_pkl(fn)
	info("ILPInstances: {}".format(len(instances)))
	train_runner(ids, 4, 66, 3, instances)


if __name__ == '__main__':
	test_train_runner()
# main()
