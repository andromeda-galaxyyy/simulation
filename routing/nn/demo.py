import math
import numpy as np
import tensorflow as tf
from tensorflow.keras.mixed_precision import experimental as mixed_precision

# policy = mixed_precision.Policy('mixed_float16')
# mixed_precision.set_policy(policy)

if __name__ == '__main__':

    x = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y = np.array([[0], [1], [1], [0]])

    loss_function = tf.keras.losses.BinaryCrossentropy()

    for i in range(2000):
        if i % 100 == 0:
            print("Iteration {}".format(i))

        model = tf.keras.Sequential([
            tf.keras.layers.Dense(units=1, activation='tanh', dtype=tf.float16)])

        model.compile(optimizer='sgd', loss=loss_function)
        model.fit(x=x, y=y, epochs=1, batch_size=1)

        loss_result = loss_function(y, model(x))

        if math.isnan(loss_result):
            raise RuntimeError('NAN Error in iteration {}'.format(i))
