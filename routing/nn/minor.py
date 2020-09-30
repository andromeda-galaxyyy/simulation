from abc import ABC

import keras
from routing.nn.sgd16 import SGDMultiType
from keras.models import Model
from keras.layers import Dense, Dropout, BatchNormalization, Input, Add
from keras.optimizers import Adam, Adagrad, Adadelta, SGD
import keras.backend as K
from routing.nn.dataset_generator import ILPGenerator
from numpy.core.multiarray import ndarray
import numpy  as np
import tensorflow as tf
from utils.file_utils import load_json, load_pkl, save_pkl
from utils.log_utils import debug, info, err
from routing.nn.base import Routing
from keras.models import load_model
import os
from path_utils import get_prj_root
from keras.callbacks import ModelCheckpoint
from routing.nn.common import persist_dir
from routing.instance import RoutingInput, RoutingOutput
from typing import Tuple, List, Dict

tf.config.experimental_run_functions_eagerly(True)

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
	try:
		# Currently, memory growth needs to be the same across GPUs
		for gpu in gpus:
			tf.config.experimental.set_memory_growth(gpu, True)
	except RuntimeError as e:
		err(e)


class Minor(Routing):
	def __init__(self, id_, num_nodes: int, num_flows: int, num_ksp: int):
		super(Minor, self).__init__(id_)
		self.n_nodes = num_nodes
		self.n_flows = num_flows
		self.n_ksp = num_ksp
		self.model: Model = None
		self.lr = 0.0001
		self.decay = 1e-4

		self.feature_dim = self.n_flows * (self.n_nodes - 1) * self.n_nodes
		self.output_dim = self.n_ksp * (self.n_nodes - 1)

	def fit(self,
	        train: Tuple[np.ndarray, np.ndarray],
	        test: Tuple[np.ndarray, np.ndarray]
	        ):

		history = None
		ckt_fn = os.path.join(persist_dir, "minor.{}.hdf5".format(self.id_))
		checkpoint = ModelCheckpoint(ckt_fn,
		                             monitor="val_loss",
		                             verbose=1,
		                             save_best_only=True,
		                             mode="auto",
		                             period=1
		                             )

		early_stop = tf.keras.callbacks.EarlyStopping(
			monitor="val_loss",
			min_delta=0,
			patience=3,
			verbose=1,
			mode="min",
			baseline=None,
			restore_best_weights=True,
		)

		if True:
			assert len(train) == 2
			assert len(test) == 2
			# instance
			x, y = train
			assert len(x) == len(y)

			self.assert_shape(x)
			self.assert_shape(y, False)

			xx, yy = test
			assert len(xx) == len(yy)
			self.assert_shape(xx)
			self.assert_shape(yy, False)

			info("Minor model loaded {} train instances".format(len(x)))
			info("Minor model loaded {} test instances".format(len(xx)))

			outputs = {}
			test_outputs = {}
			for idx in range(self.n_flows):
				name = "output{}".format(idx)
				outputs[name] = y[:, idx, :]
				test_outputs[name] = yy[:, idx, :]

			history = self.model.fit(
				x,
				outputs,
				epochs=20,
				batch_size=32,
				validation_data=(xx, test_outputs),
				callbacks=[checkpoint, early_stop]
			)

		debug("Minor model {} prepare to fit".format(self.id_))

		history_fn = os.path.join(persist_dir, "minor.{}.history.pkl".format(self.id_))
		save_pkl(history_fn, history.history)
		debug("Minor model {} history saved to {}".format(self.id_, history_fn))

	def fit_with_generator(self,
	                       train_generator: ILPGenerator,
	                       validate_generator: ILPGenerator):
		ckt_fn = os.path.join(persist_dir, "minor.{}.hdf5".format(self.id_))
		checkpoint = ModelCheckpoint(ckt_fn,
		                             monitor="val_loss",
		                             verbose=1,
		                             save_best_only=True,
		                             mode="auto",
		                             period=1
		                             )

		early_stop = tf.keras.callbacks.EarlyStopping(
			monitor="val_loss",
			min_delta=0,
			patience=3,
			verbose=1,
			mode="min",
			baseline=None,
			restore_best_weights=True,
		)
		history = self.model.fit_generator(
			generator=train_generator,
			epochs=20,
			verbose=1,
			callbacks=[checkpoint, early_stop],
			validation_data=validate_generator,
			# use_multiprocessing=True
		)

		debug("Minor model {} prepare to fit".format(self.id_))

		history_fn = os.path.join(persist_dir, "minor.{}.history.pkl".format(self.id_))
		save_pkl(history_fn, history.history)
		debug("Minor model {} history saved to {}".format(self.id_, history_fn))

	def fit_with_dataset(self,
	                     train_dataset: tf.data.Dataset,
	                     validate_dataset: tf.data.Dataset,
	                     ):
		ckt_fn = os.path.join(persist_dir, "minor.{}.hdf5".format(self.id_))
		checkpoint = ModelCheckpoint(ckt_fn,
		                             monitor="val_loss",
		                             verbose=1,
		                             save_best_only=True,
		                             mode="auto",
		                             period=1
		                             )

		early_stop = tf.keras.callbacks.EarlyStopping(
			monitor="val_loss",
			min_delta=0,
			patience=3,
			verbose=1,
			mode="min",
			baseline=None,
			restore_best_weights=True,
		)
		history = self.model.fit(
			train_dataset,
			epochs=20,
			verbose=1,
			callbacks=[checkpoint, early_stop],
			validation_data=validate_dataset,
		)

		debug("Minor model {} prepare to fit".format(self.id_))

		history_fn = os.path.join(persist_dir, "minor.{}.history.pkl".format(self.id_))
		save_pkl(history_fn, history.history)
		debug("Minor model {} history saved to {}".format(self.id_, history_fn))

	def __do_build(self):
		feature_dim = self.feature_dim
		output_dim = self.output_dim

		# x shape
		# instance,N*(N-1)*n_flows
		# output shape
		# instance,(n_nodes-1)*ksp
		inp = Input(shape=(feature_dim,))
		x = BatchNormalization()(inp)
		# x=inp
		x = Dense(units=feature_dim // 4,
		          activation="relu",
		          input_shape=(feature_dim,), )(x)

		# x = BatchNormalization()(x)
		x = Dense(units=feature_dim // 4,
		          activation="relu",
		          input_shape=(feature_dim // 4,), )(x)

		x = Dense(units=feature_dim // 4,
		          activation="relu",
		          input_shape=(feature_dim // 8,), )(x)
		x = BatchNormalization()(x)
		# y = x

		x = Dense(units=feature_dim // 4,
		          activation="relu",
		          input_shape=(feature_dim // 4,), )(x)
		# x = BatchNormalization()(x)
		# x = Add()([y, x])
		x = Dense(units=feature_dim // 4,
		          activation="relu",
		          input_shape=(feature_dim // 4,), )(x)

		outputs = {}
		losses = {}
		weights = {}
		metrics = {}
		for idx in range(self.n_flows):
			name = "output{}".format(idx)
			o = Dense(units=output_dim,
			          activation=self.softmax,
			          input_dim=(feature_dim // 4,),
			          name="output{}".format(idx))(x)
			outputs[name] = o
			weights[name] = 1
			losses[name] = self.cost
			metrics[name] = self.metric

		adam = Adam(self.lr, self.decay)
		# sgd=SGD(self.lr,nesterov=True,momentum=0.9)
		strategy = tf.distribute.MirroredStrategy()
		n_replicas = strategy.num_replicas_in_sync
		info("Number of devices:{}".format(n_replicas))

		self.model = Model(inp, list(outputs.values()))
		self.model.compile(
			loss=losses,
			loss_weights=weights,
			optimizer=adam,
			metrics=metrics
		)

		debug("Minor model id: {} compiled".format(self.id_))
		self.model.summary()

	def build(self):
		# strategy = tf.distribute.MirroredStrategy()
		# n_replicas = strategy.num_replicas_in_sync
		# info("Number of devices:{}".format(n_replicas))
		# if n_replicas>1:
		# 	with strategy.scope():
		# 		self.__do_build()
		# else:
		self.__do_build()

	def predict(self, data):
		# data shape
		# (instance,N*(N-1)*n_flows)
		self.assert_shape(data)
		info("Predict input {} instances".format(len(data)))
		# return shape
		# (instance,n_flows,N-1)

		raw = self.model.predict(data, batch_size=4, verbose=1)
		raw = np.asarray(raw)
		# print(raw.shape)

		instance = len(data)
		# (instance,n_flows,(N-1),n_ksp)
		raw = raw.reshape((instance, self.n_flows, self.n_nodes - 1, self.n_ksp))
		# reshape to (instance,n_flows,N-1)
		return raw.argmax(-1)

	def save_model(self, f_n=None):
		if f_n is None:
			f_n = os.path.join(persist_dir, "minor.{}.hdf5".format(self.id_))

		debug("Minor model id:{} save model to {}".format(self.id_, f_n))
		self.model.save(f_n)

	def load_model(self, fn=None):
		if fn is None:
			fn = os.path.join(persist_dir, "minor.{}.hdf5".format(self.id_))
		self.model = load_model(fn, custom_objects={
			"cost": self.cost,
			"softmax": self.softmax,
			"metric": self.metric
		})

	def plot(self, fn=None):
		pass

	def assert_shape(self, data: np.ndarray, is_x: bool = True):
		# x shape (n_instance,n_ksp*(n_nodes-1)*n_nodes)
		# y shape (n_instance,n_flows,n_nodes-1)
		# y不是one-hot编码
		shape = data.shape
		assert len(shape) >= 2
		if is_x:
			# print(shape[1])
			assert shape[1] == self.n_flows * (self.n_nodes - 1) * self.n_nodes
			return

		# y_shape=(instance,n_flows,N-1)
		assert shape[1] == self.n_flows
		assert shape[2] == self.n_nodes - 1

	def cost(self, y_true, y_predict):
		# y_true shape (instance,(n_nodes-1))
		# y_predict shape(instance,n_nodes-1,ksp)
		y_true = K.reshape(y_true, (-1, self.n_nodes - 1))
		y_predict = K.reshape(y_predict, (-1, self.n_nodes - 1, self.n_ksp))

		res = K.sum(K.sparse_categorical_crossentropy(y_true, y_predict))
		return res

	def softmax(self, t):
		# instance,(n_nodes-1)*ksp
		k = self.n_ksp
		tmp = K.reshape(t, (-1, (self.n_nodes - 1), k))
		# instance,(n_node-1),ksp
		# return K.softmax(tmp, -1)
		return K.reshape(K.softmax(tmp, -1), (-1, (self.n_nodes - 1) * self.n_ksp))

	def metric(self, y_true, y_predict):
		# y_true shape (instance,(n_nodes-1))
		# y_predict shape(instance,n_nodes-1,ksp)
		y_true = K.reshape(y_true, (-1, self.n_nodes - 1))
		y_predict = K.reshape(y_predict, (-1, self.n_nodes - 1, self.n_ksp))
		# m=tf.keras.metrics.SparseCategoricalAccuracy()
		# m.update_state(y_true,y_predict)
		return tf.metrics.sparse_categorical_accuracy(y_true, y_predict)


def test_minor():
	pass


if __name__ == '__main__':
	test_minor()

# 	N = 66
# 	n_flows = 4
# 	n_instance = 4
# 	n_ksp = 3
# 	x_train = 100 * np.random.rand(n_instance, N * (N - 1) * n_flows)
# 	x_test = 100 * np.random.rand(n_instance, N * (N - 1) * n_flows)
# 	# y_train=np.asarray([0.1,0.2,0.7])
#
# 	# shape (n_instance,n_flows,(N-1))
# 	y_train = np.asarray(
# 		[[[2 for _ in range(N - 1)] for _ in range(n_flows)] for _ in range(n_instance)])
# 	print(y_train.shape)
# 	y_test = y_train
# 	model = Minor(1, N, n_flows, n_ksp)
# 	model.build()
# 	model.fit((x_train, y_train), (x_test, y_test))
# 	fn = "/tmp/model.hdf5"
# 	model.save_model(fn)
# 	model.plot()
#
# 	model = Minor(1, N, n_flows, n_ksp)
#
# 	model.load_model(fn)
# 	p = model.predict(x_test)
# 	print(p.shape)
# # print(p.tolist())
