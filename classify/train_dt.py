from utils.common_utils import *
from argparse import ArgumentParser
from collections import namedtuple
from typing import List, Dict
from path_utils import get_prj_root
from classify.model import DT
from datetime import datetime
import numpy as np

random.seed(datetime.now())

Instance = namedtuple("Instance", ["features", "label"])

win_size = 10
limit = 100000

dirs = {
	"iot": "/tmp/flow_pkts",
	"video": "/tmp/video"
}
instances_dir = os.path.join(get_prj_root(), "classify/instances")


def gen_single_instance(dirname, flow, flow_type):
	def extract_features(raw_features: List[float]):
		extracted_features = []
		raw_features = [r for r in raw_features if int(r) != 0]

		extracted_features.append(min(raw_features))
		extracted_features.append(max(raw_features))
		extracted_features.append(sum(raw_features) / len(raw_features))
		extracted_features.append(np.std(raw_features))
		return extracted_features

	features = []
	idts = []
	ps = []
	idt_file = os.path.join(dirname, flow["idt"])
	ps_file = os.path.join(dirname, flow["ps"])
	with open(idt_file, 'r') as fp:
		lines = fp.readlines()
		fp.close()
	lines = [l.strip() for l in lines]
	lines = [l for l in lines if l != "" and l != "\n"]
	if len(lines) < win_size:
		return None
	lines = lines[:win_size]
	for l in lines:
		idts.append(float(l))

	with open(ps_file, "r") as fp:
		lines = fp.readlines()
		fp.close()
	if len(lines) < win_size:
		return None
	lines = [l.strip() for l in lines]
	lines = [l for l in lines if l != "" and l != "\n"]
	lines = lines[:win_size]
	for l in lines:
		ps.append(float(l))

	# 有很奇怪的现象
	ps = [p for p in ps if p != 0]
	if len(ps) == 0:
		print(flow["ps"])
		return None
	# assert len(ps)!=0
	idts = [i for i in idts if int(i) != 0]
	if len(idts) == 0:
		print(flow["idt"])
		return None

	features.extend(extract_features(ps))
	features.extend(extract_features(idts))
	if flow_type == "iot":
		label = 1
	else:
		label = 0
	return Instance(features=features, label=label)


def generate():
	instances_dir = os.path.join(get_prj_root(), "classify/instances")
	for flow_type, dirname in dirs.items():
		statistics = load_json(os.path.join(dirname, "statistics.json"))
		flows: List = statistics["flows"]
		sorted(flows, key=lambda f: -f["num_pkt"])
		if len(flows) > limit:
			flows = flows[:limit]
		instances = [gen_single_instance(dirname, f, flow_type) for f in flows]
		instances = [i for i in instances if i is not None]
		print(len(instances))
		save_pkl(os.path.join(instances_dir, "{}.pkl".format(flow_type)), instances)


def train_and_predict():
	iot = load_pkl(os.path.join(instances_dir, "iot.pkl"))
	videos = load_pkl(os.path.join(instances_dir, "video.pkl"))
	for i in iot:
		assert i.label == 1
	for i in videos:
		assert i.label == 0
	debug("# iot instances {}".format(len(iot)))
	debug("# video instances {}".format(len(videos)))
	random.shuffle(iot)
	random.shuffle(videos)
	# train 3:1
	iot_train = iot[:20000]
	info("#iot train {}".format(len(iot_train)))
	video_train = videos[:300]
	info("#video train {}".format(len(video_train)))

	train = []
	train.extend(iot_train)
	train.extend(video_train)
	train_x = [x.features for x in train]
	train_y = [x.label for x in train]

	# test 1:1
	test = []
	iot_test = iot[20000:20086]
	info("#iot test {}".format(len(iot_test)))
	video_test = videos[300:]
	info("#video test {}".format(len(video_test)))

	test.extend(iot_test)
	test.extend(video_test)

	test_x = [t.features for t in test]
	test_y = [t.label for t in test]
	# print(len([t.label for t in test if t.label==0]))

	dt = DT()
	dt.fit((train_x, train_y))
	predicts = dt.predict(test_x)
	count = 0
	for idx in range(len(test_x)):
		if int(predicts[idx]) == int(test_y[idx]):
			count += 1
	print(count / len(test_x))


if __name__ == '__main__':
	parser = ArgumentParser()
	print("running mode\n"
	      "1. generate instances\n"
	      "2. train dt\n")
	parser.add_argument("--mode", type=int, default=2)
	args = parser.parse_args()
	mode = int(args.mode)
	if mode == 1:
		generate()
	elif mode == 2:
		train_and_predict()
