from utils.common_utils import load_pkl,save_pkl, info

import matplotlib.pyplot as plt
import numpy as np
from routing.ksp import NetworkTopo
import os
from typing import List,Dict,Tuple


src_dsts=[(i,j) for i in range(66) for j in range(66)]
src_dsts=list(filter(lambda x:x[0]!=x[1],src_dsts))

def qos(topo:NetworkTopo, demands: List[Tuple],solution:List[int],ksps:Dict[Tuple,List]):
	g=topo.g
	volumes=[d[0] for d in demands]
	delays=[d[1] for d in demands]
	assert len(volumes)==len(src_dsts)
	assert len(delays)==len(src_dsts)
	assert len(solution)==len(src_dsts)
	if ksps is None:
		ksps=load_pkl("topo/ksp_0.pkl")

	edge_capacities=[]
	edges=list(g.edges(data=True))
	traffic=[0 for _ in range(g.number_of_edges())]
	utilities=[0 for _ in range(g.number_of_edges())]
	for j in range(g.number_of_edges()):
		u,v,spec =edges[j]
		edge_capacities.append(spec["capacity"])
		for i,(src,dst) in enumerate(src_dsts):
			path=ksps[(src,dst)][solution[i]]
			if topo.edge_in_path(u,v,path):
				traffic[j]+=volumes[i]
		utilities[j]=traffic[j]/edge_capacities[j]

	flow_delays=[0 for _ in range(len(src_dsts))]
	for i,(src,dst) in enumerate(src_dsts):
		path=ksps[(src,dst)][solution[i]]
		for u,v in list(zip(path[:-1],path[1:])):
			flow_delays[i]+=g.edges[u,v]["delay"]

	return utilities,flow_delays
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
	topos = load_pkl("topo/topo.pkl")
	topo = NetworkTopo(topos[0])
	ksp = load_pkl("topo/ksp_0.pkl")
	# model: Model = load_model("hdf5/best_model2.hdf5",custom_objects={"custom_softmax":custom_softmax,"custom_cost":custom_cost})
	# logger.info("nn model loaded")
	stats = []

	for file in os.listdir("labels/0"):
		if ".pkl" not in file: continue
		if len(file) > 10: continue
		solutions = []
		info("start to check instance {}".format(file))
		data = load_pkl(os.path.join("labels/0", file))
		demands = data[0]
		required_delays = [d[1] for d in demands]
		res = data[2]
		for i in range(66 * 65):
			tmp = res[i * 5:(i + 1) * 5]
			solutions.append(tmp.index(max(tmp)))
		utilities, _ = qos(topo, demands, solutions, ksp)
		max_utility = max(utilities)

		ospf_solutions = [0 for _ in range(66 * 65)]
		ospf_utilities, ospf_delays = qos(topo, demands, ospf_solutions, ksp)
		diff_utility = (max(ospf_utilities) - max_utility) / max_utility
		diff_delays = [ospf_delays[i] - required_delays[i] for i in range(66 * 65)]
		stats.append((diff_utility, diff_delays))

	# volume_model = [d[0] for d in demands]
	# volume_model = normalize(volume_model)
	# delay_model = [d[1] for d in demands]
	# delay_model = normalize(delay_model)
	# input_data = []
	# input_data.extend(volume_model)
	# input_data.extend(delay_model)
	# input_data = np.asarray([input_data])
	#
	# y = model.predict(input_data)[0].tolist()
	# predictions = []
	# for i in range(66 * 65):
	# 	tmp = y[i * 5:(i + 1) * 5]
	# 	predictions.append(tmp.index(max(tmp)))
	# pre_utilities, pre_flow_delays = qos(topo, demands, predictions, ksp)
	# diff_utility = max(pre_utilities) - max_utility
	# diff_delays = [pre_flow_delays[i] - required_delays[i] for i in range(66 * 65)]
	# stats.append((diff_utility, diff_delays))
	save_pkl("/tmp/ospf.pkl", stats)
	pass

def nn_model():
	pass


def plot_train_loss(history_fn="/tmp/history2.pkl"):
	'''
	plot model loss
	:return:
	'''
	history = load_pkl("/tmp/history2.pkl")
	plt.plot(history['loss'])
	plt.plot(history['val_loss'])
	plt.title('Model loss')
	plt.ylabel('Loss')
	plt.xlabel('Epoch')
	plt.legend(['Train', 'Test'], loc='upper left')
	plt.show()

if __name__ == '__main__':
	pass
