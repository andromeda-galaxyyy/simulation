from abc import ABC

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
from routing.nn.base import Routing
import tensorflow as tf

Instance = namedtuple("Instance", "features labels")

module_dir = os.path.join(get_prj_root(), "routing")

models_dir = os.path.join(get_prj_root(), "routing/nn")


class Monolithic(Routing):
	def __init__(self, id_, num_nodes: int, num_flows: int, num_ksp: int):
		super(Monolithic, self).__init__(id_)
		self.n_nodes: int = num_nodes
		self.n_flows: int = num_flows
		self.n_ksp: int = num_ksp
		self.model: Model = None

	def softmax(self, data):
		# data ninstance,(n_ndoes-1)*n_nodes*k
		k = self.n_ksp
		N = self.n_nodes
		tmp = K.reshape(data, (-1, (N - 1) * N, k))
		return K.reshape(K.softmax(tmp, -1), (-1, (N - 1) * N * k))

	def metric(self, y_true, y_predict):
		k = self.n_ksp
		N = self.n_nodes
		y_true = K.reshape(y_true, (-1, N * (N - 1)))
		y_predict = K.reshape(y_predict, (-1, N * (N - 1), k))
		return tf.metrics.sparse_categorical_crossentropy(y_true, y_predict)

	def cost(self, y_true, y_predict):
		k = self.n_ksp
		N = self.n_nodes
		y_true = K.reshape(y_true, (-1, (N - 1) * N))
		y_predict = K.reshape(y_predict, (-1, N * (N - 1), k))
		return K.sum(K.sparse_categorical_crossentropy(y_true, y_predict))

	def build(self):
		feature_dim = self.n_flows * (self.n_nodes - 1) * self.n_nodes
		output_dim = self.n_nodes * (self.n_nodes - 1) * self.n_ksp
		inp = Input(shape=(feature_dim,))
		x = BatchNormalization()(inp)
		x = Dense(units=feature_dim//4,
		          activation="relu",
		          input_shape=(feature_dim//4,))(x)
		outputs = {}
		losses = {}
		weights = {}
		metrics = {}

		for flow_idx in range(self.n_flows):
			name = "output{}".format(flow_idx)
			o = Dense(
				units=output_dim,
				activation=self.softmax,
				input_dim=(feature_dim//4,),
				name="output{}".format(flow_idx)
			)(x)
			outputs[name] = o
			weights[name] = 1
			losses[name] = self.cost
			metrics[name] = self.metric

		self.model = Model(inp, list(outputs.values()))
		opt = Adam()
		self.model.compile(
			loss=losses,
			loss_weights=weights,
			optimizer=opt,
			metrics=metrics,
		)
		debug("Monolithic model compiled")
		self.model.summary()

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
		self.assert_shape(x_train)
		self.assert_shape(y_train, False)

		x_validate, y_validate = test
		assert len(x_validate) == len(y_validate)
		self.assert_shape(x_validate)
		self.assert_shape(y_validate, False)

		debug("loaded {} train instances".format(len(x_train)))
		debug("loaded {} test instances".format(len(x_validate)))
		ckt_fn = os.path.join(models_dir, "{}.hdf5".format(self.id_))

		checkpoint = ModelCheckpoint(ckt_fn,
		                             monitor="loss",
		                             verbose=1, save_best_only=True,
		                             mode="auto",
		                             period=1)
		debug("data prepared starting to fit")
		outputs = {}
		validate_outputs = {}
		for idx in range(self.n_flows):
			name = "output{}".format(idx)
			outputs[name] = y_train[:,idx, :]
			validate_outputs[name] = y_validate[:, idx, :]

		history = self.model.fit(
			x_train,
			outputs,
			epochs=10,
			batch_size=32,
			validation_data=(x_validate, validate_outputs),
			callbacks=[checkpoint]
		)
		history_fn = os.path.join(models_dir, "history_{}.pkl".format(self.id_))
		save_pkl(history_fn, history.history)
		debug("Monolithic model {} history saved to {}".format(self.id_, history_fn))

	def predict(self, data):
		self.assert_shape(data)
		info("Predict input {} instances".format(len(data)))
		raw = self.model.predict(data, batch_size=4, verbose=1)
		raw = np.asarray(raw)
		instance = len(data)
		raw = raw.reshape((instance, self.n_flows, self.n_nodes * (self.n_nodes - 1), self.n_ksp))
		return raw.argmax(-1)

	def save_model(self, fn=None):
		if fn is None:
			fn = os.path.join(models_dir, "{}.hdf5".format(self.id))
		self.model.save(fn)

	def load_model(self, fn=None):
		if fn is None:
			fn = os.path.join(models_dir, "{}.hdf5".format(self.id))
		check_file(fn)
		self.model = load_model(fn, custom_objects={"softmax":self.softmax,
		                                            "cost":self.cost,
		                                            "metric":self.metric})

	def assert_shape(self, data: np.ndarray, is_x: bool = True):
		shape = data.shape
		assert len(data) >= 2
		if is_x:
			assert shape[1] == self.n_flows * (self.n_nodes - 1) * self.n_nodes
			return

		# y_shape==(instance,n_flows,(n-1)*n)
		assert shape[1] == self.n_flows
		assert shape[2] == self.n_nodes * (self.n_nodes - 1)

	def plot(self, fn):
		pass


if __name__ == '__main__':
	N = 66
	n_flows = 4
	n_instance = 4
	n_ksp = 3
	x = 100 * np.random.rand(n_instance, N * (N - 1) * n_flows)
	y=np.asarray(
		[[[2 for _ in range(N*(N-1))] for _ in range(n_flows)] for _ in range(n_instance)]
	)
	model=Monolithic(1,N,n_flows,n_ksp)
	model.build()
	model.fit((x,y),(x,y))
	fn = "/tmp/model.hdf5"
	model.save_model(fn)

	model = Monolithic(1, N, n_flows, n_ksp)

	model.load_model(fn)
	p = model.predict(x)
	print(p.shape)
