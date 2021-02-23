from keras.models import Model
from keras.layers import Dense, BatchNormalization, Input
from keras.optimizers import Adam
import keras.backend as K
from routing.nn.dataset_generator import ILPGenerator
import numpy as np
import tensorflow as tf
from utils.file_utils import save_pkl
from utils.log_utils import debug, info, err
from keras.models import load_model
import os
from sockets.server import recvall2
from keras.callbacks import ModelCheckpoint
from typing import Tuple
import gc
from path_utils import get_prj_root
import socket
import json


class NN3:
	def __init__(self, id_: int, num_ksps: int = 5, num_target: int = 14, num_nodes: int = 100):
		self.id_ = id_
		self.num_ksps = num_ksps
		self.feature_dim = num_nodes * (num_nodes - 1)
		self.output_dim = num_ksps * num_target
		self.model: Model = None
		self.num_target = num_target
		self.lr = 0.0001
		self.decay = 1e-5

	def softmax(self, t):
		# k = self.num_ksps
		tmp = K.reshape(t, (-1, self.num_target, self.num_ksps))
		return K.reshape(K.softmax(tmp, -1), (-1, self.num_target * self.num_ksps))

	def metric(self, y_true, y_predict):
		y_true = K.reshape(y_true, (-1, self.num_target))
		y_predict = K.reshape(y_predict, (-1, self.num_target, self.num_ksps))
		return tf.metrics.sparse_categorical_accuracy(y_true, y_predict)

	def cost(self, y_true, y_predict):
		y_true = K.reshape(y_true, (-1, self.num_target))
		y_predict = K.reshape(y_predict, (-1, self.num_target, self.num_ksps))
		res = K.sum(K.sparse_categorical_crossentropy(y_true, y_predict))
		return res

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
		          input_shape=(feature_dim // 4,), )(x)
		x = BatchNormalization()(x)
		# y = x

		x = Dense(units=feature_dim // 4,
		          activation="relu",
		          input_shape=(feature_dim // 4,), )(x)
		# x = BatchNormalization()(x)
		# x = Add()([y, x])
		# x=BatchNormalization()(x)
		x = Dense(units=feature_dim // 4,
		          activation="relu",
		          input_shape=(feature_dim // 4,), )(x)
		o = Dense(units=output_dim,
		          activation=self.softmax,
		          input_dim=(feature_dim // 4),
		          )(x)

		adam = Adam(self.lr, self.decay)
		strategy = tf.distribute.MirroredStrategy()
		n_replicas = strategy.num_replicas_in_sync
		info("Number of devices:{}".format(n_replicas))

		self.model = Model(inp, o)
		self.model.compile(
			loss=self.cost,
			optimizer=adam,
			metrics=self.metric,
		)

		debug("Minor model id: {} compiled".format(self.id_))
		self.model.summary()

	def build(self):
		self.__do_build()

	def fit_with_generator(self, train_dataset: tf.data.Dataset, validate_dataset: tf.data.Dataset):
		model_dir = os.path.join(get_prj_root(), "routing/nn3/nns")
		debug("model persist dir {}".format(model_dir))
		model_id = self.id_
		ckt_fn = os.path.join(model_dir, "{}.ckt.hdf5".format(self.id_))
		ckpt = ModelCheckpoint(ckt_fn, monitor="val_loss", verbose=1, save_best_only=True,
		                       mode="auto", period=1)
		early_stop = tf.keras.callbacks.EarlyStopping(
			monitor="val_loss",
			min_delta=0,
			patience=3,
			verbose=1,
			mode="min",
			baseline=None,
			restore_best_weights=True
		)
		debug("model {} prepare to fit".format(model_id))
		history = self.model.fit(
			train_dataset,
			epochs=15,
			verbose=1,
			callbacks=[ckpt, early_stop],
			validation_data=validate_dataset,
		)
		debug("model {} fit done".format(model_id))
		history_dir = model_dir
		history_fn = os.path.join(history_dir, "{}.history.pkl".format(model_id))
		save_pkl(history_fn, history.history)
		debug("model {} history saved to {}".format(model_id, history_fn))

	def save_model(self):
		model_id = self.id_
		model_dir = os.path.join(get_prj_root(), "routing/nn3/nns")
		fn = os.path.join(model_dir, "{}.hdf5".format(model_id))
		self.model.save(fn)
		debug("model {} saved to {}".format(model_id, fn))

	def load_model(self):
		model_id = self.id_
		model_dir = os.path.join(get_prj_root(), "routing/nn3/nns")
		fn = os.path.join(model_dir, "{}.hdf5".format(model_id))
		self.model = load_model(fn, custom_objects={
			"cost": self.cost,
			"softmax": self.softmax,
			"metric": self.metric
		})

	def predict(self, xdata):
		model_id = self.id_
		n_instances = len(xdata)
		info("predict with input {}".format(len(xdata)))

		raw = self.model.predict(xdata, batch_size=4, verbose=1)
		info("model {} predict done".format(model_id))
		raw = np.asarray(raw)
		raw = raw.reshape((n_instances, self.num_target, self.num_ksps))
		return raw.argmax(-1)


class Worker:
	def __init__(self, model_id: int):
		self.model_id = model_id
		info("loading model {}".format(model_id))
		self.model: NN3 = NN3(model_id)
		self.model.load_model()
		info("loading model done {}".format(model_id))

		self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock_fn = os.path.join("/tmp/{}.sock".format(self.model_id))
		self.sock_fn=sock_fn
		if os.path.exists(sock_fn):
			os.remove(sock_fn)
		self.server.bind(sock_fn)

	def start(self):
		model_id=self.model_id
		self.server.listen()
		debug("worker {} listen to {}".format(model_id,self.sock_fn))
		while True:
			conn, _ = self.server.accept()
			debug("new connection")
			req = recvall2(conn)
			debug("received done")
			volumes = json.loads(req)["volumes"]
			assert len(volumes)==100*99
			actions=self.model.predict(np.asarray([volumes]))[0].tolist()
			resp={
				"res":actions
			}
			conn.sendall(bytes(json.dumps(resp) + "*", "ascii"))
			conn.close()


if __name__ == '__main__':
	import argparse
	parser=argparse.ArgumentParser()
	parser.add_argument("--model_id",type=int,default=0)
	args=parser.parse_args()
	model_id=int(args.model_id)
	debug("starting model {} server".format(model_id))
	server=Worker(model_id)
	server.start()
