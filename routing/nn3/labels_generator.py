from keras.utils import Sequence
from typing import Tuple, List
from utils.file_utils import *
import numpy as np
import tensorflow as tf
from routing.nn3.models import *
from routing.nn3.contants import *

# modelid_to_targets = {
# 	0: [18, 20, 22, 24, 26, 28, 40, 42, 44, 46, 48, 50],
# 	2: [18, 20, 22, 24, 26, 28, 40, 42, 44, 46, 48, 50],
# 	4: [18, 20, 22, 24, 26, 28, 40, 42, 44, 46, 48, 50],
# 	6: [62, 64, 66, 68, 70, 72, 84, 86, 88, 90, 92, 94],
# 	8: [62, 64, 66, 68, 70, 72, 84, 86, 88, 90, 92, 94],
# 	10: [62, 64, 66, 68, 70, 72, 84, 86, 88, 90, 92, 94],
# 	18: [40, 42, 44, 46, 48, 50, 33, 32, 31, 30, 29, 28, 27, 26],
# 	19: [40, 42, 44, 46, 48, 50, 33, 32, 31, 30, 29, 28, 27, 26],
# 	20: [40, 42, 44, 46, 48, 50, 33, 32, 31, 30, 29, 28, 27, 26],
# }
#
# idx = 0
# flattenidxes = {}
#
# for i in range(100):
# 	for j in range(100):
# 		if i == j: continue
# 		flattenidxes[(i, j)] = idx
# 		idx += 1
#
# assert idx == 100 * 99


def get_labels_generators(fns: List[str], model_id: int, batch_size=32):
	def mapper(instance: Routing):
		traffic = instance.traffic
		labels=instance.labels
		indexes = []
		old_targets_length = len(modelid_to_targets[model_id])
		targets = modelid_to_targets[model_id]
		for t in targets:
			indexes.append(labels[flattenidxes[(model_id, t)]])
		for _ in range(old_targets_length, 14):
			indexes.append(0)
		assert len(indexes) == 14
		return np.asarray(traffic), np.asarray(indexes)

	def loader():
		for fn in fns:
			instances = load_pkl(fn)
			for routing in instances:
				yield mapper(routing)

	dataset = tf.data.Dataset.from_generator(generator=loader, output_types=(tf.float32, tf.int8))
	dataset = dataset.batch(batch_size)
	dataset = dataset.cache()

	return dataset
