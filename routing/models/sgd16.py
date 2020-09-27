import keras.backend as K
from keras.optimizers import SGD

#https://www.kaggle.com/danmoller/keras-training-with-float16-test-kernel-1
# Comments added to parts of the code changed from original
class SGDMultiType(SGD):

	def get_updates(self, loss, params):
		grads = self.get_gradients(loss, params)
		self.updates = [K.update_add(self.iterations, 1)]

		lr = self.lr
		if self.initial_decay > 0:
			lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
			                                          K.dtype(self.decay))))

		# Adjusting learning rate for matching each weight type
		learning_rates = [K.cast(lr, K.dtype(p)) for p in params]

		# momentum
		shapes = [K.int_shape(p) for p in params]

		# adding custom types to moments
		moments = [K.zeros(shape, dtype=K.dtype(p)) for p, shape in zip(params, shapes)]
		self.weights = [self.iterations] + moments

		# adjusting "self.momentum" value to weight types
		momentums = [K.cast(self.momentum, K.dtype(p)) for p in params]

		# using the typed learning rate and momentums
		for p, g, m, lr, momentum in zip(params, grads, moments, learning_rates, momentums):
			v = momentum * m - lr * g  # velocity
			self.updates.append(K.update(m, v))

			if self.nesterov:
				new_p = p + momentum * v - lr * g
			else:
				new_p = p + v

			# Apply constraints.
			if getattr(p, 'constraint', None) is not None:
				new_p = p.constraint(new_p)

			self.updates.append(K.update(p, new_p))
		return self.updates
