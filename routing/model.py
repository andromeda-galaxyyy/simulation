from keras import Sequential
import keras

class Routing:
	def __init__(self):
		pass
	def fit(self,train,test):
		raise NotImplementedError

	def predict(self,data):
		raise NotImplementedError

	def save_mode(self,fn):
		raise NotImplementedError

	def load_model(self,fn):
		raise NotImplementedError


class NN(Routing):
	def fit(self, train, test):
		pass

	def predict(self, data):
		pass

	def save_mode(self, fn):
		pass

	def load_model(self, fn):
		pass


class Dumb(Routing):
	def fit(self, train, test):
		pass

	def predict(self, data):
		pass

	def save_mode(self, fn):
		pass

	def load_model(self, fn):
		pass

if __name__ == '__main__':
    pass

