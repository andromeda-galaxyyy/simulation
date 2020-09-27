from abc import ABC

import keras
from keras.models import Sequential
from path_utils import get_prj_root
import os

models_dir=os.path.join(get_prj_root(),"routing/nn")


class RoutingModel:
	def __init__(self):
		pass

	def load_model(self,fn):
		raise NotImplementedError

	def save_model(self,fn):
		raise NotImplementedError

	def train(self,train_data,test_data=None):
		raise NotImplementedError

	def predict(self,train_data):
		raise NotImplementedError


class NN(RoutingModel):
	def load_model(self,fn):
		pass

	def save_model(self,fn):
		pass

	def train(self,train_data,test_data=None):
		pass

	def predict(self,train_data):
		pass


class Dumb(RoutingModel):

	def load_model(self, fn):
		pass

	def save_model(self, fn):
		pass

	def train(self, train_data, test_data=None):
		pass

	def predict(self, train_data):
		pass