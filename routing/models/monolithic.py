from keras import Sequential
import keras
from keras.models import Model
from keras.layers import Dense, Dropout, BatchNormalization, Input
from keras.optimizers import Adam
import keras.backend as K
from numpy.core.multiarray import ndarray

from utils.common_utils import load_pkl, load_json, debug, info, err, check_dir, check_file, \
	save_pkl
from path_utils import get_prj_root
from utils.num_utils import normalize
from keras.models import load_model
from keras.callbacks import ModelCheckpoint
import os
import numpy as np
from utils.common_utils import file_exsit, dir_exsit
import random
from argparse import ArgumentParser
from collections import namedtuple
from typing import Tuple, List, Dict
from routing.models.base import Routing

Instance = namedtuple("Instance", "features labels")

module_dir = os.path.join(get_prj_root(), "routing")

models_dir = os.path.join(get_prj_root(), "routing/models")


class Dumb(Routing):
	def __init__(self, id_="dumb"):
		super(Dumb, self).__init__(id_)

	def fit(self, train, test):
		pass

	def predict(self, data=None):
		res1 = []
		res2 = []
		demands = 66 * 65
		k = 5
		n_samples = 66 * 65 * 2
		n_classes = k
		x = np.zeros((n_samples, n_classes))
		J = np.random.choice(n_classes, n_samples)
		x[np.arange(n_samples), J] = 1
		return x[0:66 * 65], x[66 * 65:]

	def save_model(self, fn):
		pass

	def load_model(self, fn):
		pass


class NN(Routing):
	def __init__(self, num_of_action=66 * 65 * 2, id_="NN", mode="train"):
		super(NN, self).__init__(id_)
		self.num_of_action = num_of_action
		self.action_dim = 5
		self.model: keras.models.Model = None
		if mode == "train":
			self.__build_model()
		else:
			fn = os.path.join(models_dir, "{}.hdf5".format(self.id))
			self.load_model(fn)

	def __build_model(self):
		feature_dim = self.num_of_action
		inp = Input(shape=(feature_dim,))
		x = Dense(units=feature_dim * 2, activation="relu", input_shape=(feature_dim,))(inp)

		x = BatchNormalization()(x)
		x = Dense(units=feature_dim, activation="relu", input_shape=(feature_dim * 2,))(x)

		x = Dense(units=8192, activation="relu", input_shape=(feature_dim,))(x)
		x = BatchNormalization()(x)
		x = Dense(units=8192, activation="relu", input_shape=(8192,))(x)
		x = Dropout(rate=0.1)(x)
		# model.add(Dense(units=8192,activation="relu",input_shape=(8192,)))
		# model.add(Dense(units=8192,activation="relu",input_shape=(8192,)))

		x = Dense(units=feature_dim, activation="relu", input_shape=(8192,))(x)

		output1 = Dense(units=feature_dim // 2 * 5, activation=NN.custom_softmax,
		                input_dim=(feature_dim,), name="output1")(x)
		output2 = Dense(units=feature_dim // 2 * 5, activation=NN.custom_softmax,
		                input_dim=(feature_dim,), name="output2")(x)
		self.model = Model(inp, [output1, output2])

		adam = Adam(lr=0.001, decay=1e-6)
		self.model.compile(
			loss={"output1": NN.custom_cost, "output2": NN.custom_cost},
			loss_weights={"output1": 1, "output2": 1},
			optimizer=adam,
			metrics=["mse"])

		debug("model compiled")

	@staticmethod
	def custom_softmax(t):
		sh = K.shape(t)
		k = 5
		partial_sm = []
		for i in range(66 * 65):
			partial_sm.append(K.softmax(t[:, i * k:(i + 1) * k]))
		return K.concatenate(partial_sm)

	@staticmethod
	def custom_cost(y_true, y_pred):
		y_true = K.reshape(y_true, (-1, 66 * 65, 5))
		y_pred = K.reshape(y_pred, (-1, 66 * 65, 5))
		return K.sum(K.categorical_crossentropy(y_true, y_pred))

	@staticmethod
	def sparse_cross_entropy_cost(y_true, y_pred):
		y_pred = K.reshape(y_pred, (-1, 66 * 65, 5))
		y_true = K.reshape(y_true, (-1, 66 * 65))
		return K.sum(K.sparse_categorical_crossentropy(y_true, y_pred))

	def fit(self, train, test):
		'''
		:param train: Tuple (x_train,y_train) numpy
		x_train shape:(n_samples,n_features)
		y_train shape:(n_samples,n_output*2==66*65*5*2)
		:param test: Tuple(x_test,y_test) numpy
		:return:
		'''
		x_train, y_train = train
		assert len(x_train) == len(y_train)
		y_train_1 = y_train[:, 0:66 * 65 * 5]
		y_train_2 = y_train[:, 66 * 65 * 5:]

		x_test, y_test = test
		assert len(x_test) == len(y_test)
		y_test_1 = y_test[:, 0:66 * 65 * 5]
		y_test_2 = y_test[:, 66 * 65 * 5:]

		debug("loaded {} train instances".format(len(x_train)))
		debug("loaded {} test instances".format(len(x_test)))
		ckt_fn = os.path.join(models_dir, "{}.hdf5".format(self.id))
		checkpoint = ModelCheckpoint(ckt_fn,
		                             monitor="loss",
		                             verbose=1, save_best_only=True,
		                             mode="auto",
		                             period=1)
		debug("data prepared starting to fit")
		history = self.model.fit(
			x_train,
			{"output1": y_train_1, "output2": y_train_2},
			epochs=10,
			validation_data=(x_test, {"output1": y_test_1, "output2": y_test_2}),
			callbacks=[checkpoint]
		)
		history_fn = os.path.join(models_dir, "history_{}.pkl".format(self.id))
		save_pkl(history_fn, history.history)

	def predict(self, data):
		return self.model.predict(data, verbose=1)

	def save_model(self, fn=None):
		if fn is None:
			fn = os.path.join(models_dir, "{}.hdf5".format(self.id))
		self.model.save(fn)

	def load_model(self, fn=None):
		if fn is None:
			fn = os.path.join(models_dir, "{}.hdf5".format(self.id))
		check_file(fn)
		self.model = load_model(fn, custom_objects={"custom_softmax": NN.custom_softmax,
		                                            "custom_cost": NN.custom_cost})


def map_to_instance(obj):
	tms, res, _ = obj
	assert len(tms) == 66 * 65 * 2
	assert len(res) == 66 * 65 * 2 + 2
	# discard utility and weighted
	res = res[:-2]
	tms = [t[0] for t in tms]
	# 归一化
	tms = normalize(tms)
	labels1 = []
	for x in res[0:66 * 65]:
		tmp = [0 for _ in range(5)]
		tmp[x] = 1
		labels1.extend(tmp)
	labels2 = []
	for x in res[66 * 65:]:
		tmp = [0 for _ in range(5)]
		tmp[x] = 1
		labels2.extend(tmp)
	return tms, labels1, labels2


def generate_instances(model_id="NN", map_func=map_to_instance, ratio=0.7) -> Tuple[
	Tuple[ndarray, ndarray], Tuple[ndarray, ndarray]]:
	'''
	generate nn train and test instances from raw labels
	:param ratio:
	:param map_func:
	:param model_id:
	:return: train_instances,test_instances
	train_instances: (features,label1,label2)
	'''
	instances_dir = os.path.join(module_dir, "instances/0")
	instances_fn = os.path.join(instances_dir, "instances_{}".format(model_id))
	if file_exsit(instances_fn):
		debug("instances file exists,loading")
		return load_pkl(instances_fn)
	# generate instance_fn
	raw_label_dir = os.path.join(models_dir, "raw_labels/0")
	'''
	文件夹下的每个文件都是一个raw instance 
	'''
	instances = []
	for raw_instance_fn in list(os.listdir(raw_label_dir)):
		if ".pkl" not in raw_instance_fn: continue
		'''
		每个raw_instance 的格式为 (tm,res(决策、utility、weighted_delay,obj)
		'''
		features, label1, label2 = map_func(load_pkl(os.path.join(raw_label_dir, raw_instance_fn)))
		# simpy append
		label1.extend(label2)
		#
		assert len(label1) == 66 * 65 * 10
		instance = Instance(features=features, labels=label1)
		instances.append(instance)
	random.shuffle(instances)

	n_train = int(len(instances) * ratio)
	train_instances = instances[0:n_train]
	x_train = [ins.features for ins in train_instances]
	x_train = np.asarray(x_train)
	y_train = [ins.labels for ins in train_instances]
	y_train = np.asarray(y_train)
	test_instances = instances[n_train:]
	x_test = [ins.features for ins in test_instances]
	x_test = np.asarray(x_test)
	y_test = [ins.labels for ins in test_instances]
	y_test = np.asarray(y_test)

	debug("loaded {} train instances".format(len(train_instances)))
	debug("loaded {} test instances".format(len(test_instances)))

	save_pkl(instances_fn, ((x_train, y_train), (x_test, y_test)))
	info("save instances")
	return (x_train, y_train), (x_test, y_test)


def train():
	debug("Train mode")


def test():
	debug("Test mode")


def run_demo():
	debug("Demo mode")
	n_instances = 64
	features = []
	labels = []
	for _ in range(n_instances):
		f = normalize([np.random.uniform(10, 20) for _ in range(66 * 65 * 2)])
		features.append(f)
		ll = []
		for _ in range(66 * 65):
			for _ in range(2):
				temp = [0 for _ in range(5)]
				temp[np.random.randint(0, 5)] = 1
				ll.extend(temp)
		labels.append(ll)
	# labels.append([np.random.randint(0,5) for _ in range(66*65*2)])

	features = np.asarray(features)
	labels = np.asarray(labels)
	# assert len(labels[0])==66*65*10

	train = (features[0:50], labels[0:50])
	test = (features[50:], labels[50:])

	model = NN()
	model.fit(train, test)


if __name__ == '__main__':
	parser = ArgumentParser()
	print("mode:\n"
	      "1 generate instances from raw labels\n"
	      "2 train network\n"
	      "3 test network\n"
	      "4 run train network demo")
	parser.add_argument("--mode", type=int, help="run script in which mode", default=4)
	args = parser.parse_args()
	mode = int(args.mode)
	if mode == 1:
		generate_instances()
	elif mode == 2:
		train()
	elif mode == 3:
		test()
	elif mode == 4:
		run_demo()
	else:
		err("Invalid argument")
		exit(-1)
