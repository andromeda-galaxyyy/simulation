class Routing:
	def __init__(self, id_):
		self.id_ = id_

	# train model
	def fit(self, train, test):
		raise NotImplementedError

	# def fit(self,x_train,y_train,x_test,y_test):
	# 	raise NotImplementedError

	# predict
	def predict(self, data):
		raise NotImplementedError

	# save model to disk
	def save_model(self, fn):
		raise NotImplementedError

	# load model from persistence file
	def load_model(self, fn):
		raise NotImplementedError

	# plot model
	# for nn, draw net
	def plot(self, fn):
		raise NotImplementedError

	@staticmethod
	def plot_history(self, fn):
		pass


def has_gpu():
	return False


def use_gpu():
	pass
