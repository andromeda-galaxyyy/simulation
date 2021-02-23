from routing.nn3.nn import NN3
from utils.file_utils import *
from utils.log_utils import debug, info, err
from argparse import ArgumentParser
from multiprocessing import Process
from typing import List, Dict, Tuple, Any
import numpy as np
from routing.nn3.models import *
from sklearn.preprocessing import MinMaxScaler
from path_utils import get_prj_root
import random
from routing.nn3.labels_generator import get_labels_generators
import gc

labels_dir = "/tmp/labels"


def train_with_dataset(model_id: int, instance_fns: List[str]):
	# split ratio=0.7
	split_ratio = 0.9
	info("split ratio {}".format(split_ratio))
	split_idx = int(len(instance_fns) * split_ratio)
	train_fns = instance_fns[0:split_idx]
	random.shuffle(train_fns)
	info("train fns:#{}".format(len(train_fns)))
	validate_fns = instance_fns[split_idx:]
	random.shuffle(validate_fns)
	info("validate fns:#{}".format(len(validate_fns)))

	train_generator = get_labels_generators(train_fns, model_id=model_id)
	validate_generator = get_labels_generators(validate_fns, model_id=model_id)
	model = NN3(model_id)
	model.build()
	info("Model {} start to fit".format(model_id))
	model.fit_with_generator(train_generator, validate_generator)
	info("Model {} train done".format(model_id))


def main():
	parser = ArgumentParser()
	parser.add_argument("--model_id", type=int, default=0, help="model id")
	args = parser.parse_args()
	model_id = int(args.model_id)
	fns = []
	for fn in os.listdir(labels_dir):
		if "partition" not in fn: continue
		fns.append(os.path.join(labels_dir, fn))

	info("Number of labels fns {}".format(len(fns)))
	# random.shuffle(fns)
	fns.sort()
	train_with_dataset(model_id, fns)


if __name__ == '__main__':
	main()
