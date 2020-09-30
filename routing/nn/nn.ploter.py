from utils.file_utils import *
from utils.log_utils import debug, info, err
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import numpy


def plot_history(fn: str):
	history: Dict = load_pkl(fn)
	info(history.keys())
	plt.plot(history["loss"])
	plt.xlabel("epoch")
	plt.show()


if __name__ == '__main__':
	plot_history("/tmp/minor.0.history.pkl")
