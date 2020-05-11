import pickle
from pathlib import Path
from utils.common_utils import load_pkl,save_pkl,save_json,load_json

import matplotlib.pyplot as plt
import numpy as np
from routing.model import NN

def plot_stats():
	stats=load_pkl("/tmp/ospf.pkl")
	diff_utilities=[s[0] for s in stats]
	weights = np.ones_like(diff_utilities) * 100. / len(diff_utilities)
	# delays=[min(s[1]) for s in stats]
	count=[]
	for s in stats:
		delays=[d for d in s[1] if d<=0]
		count.append(len(delays)/66/65)

	# plt.hist(count)
	plt.hist(count,weights=weights)

	# plt.hist(diff_utilities,bins=10,weights=weights,range=(0,1))
	# plt.hist(diff_utilities)
	# plt.xlabel("Diffs")
	plt.ylabel("Percentage")
	plt.show()



def ospf():
	pass

def nn_model():
	pass

if __name__ == '__main__':
    pass
