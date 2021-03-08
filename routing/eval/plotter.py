from matplotlib.pyplot import legend, plot
from routing.instance import *
import sys
import matplotlib

if "darwin" in sys.platform:
	matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
# plt.rcParams.update({'font.size': 18})
from utils.time_utils import now_in_milli
import random
import numpy as np

random.seed(now_in_milli())


def plot_cdf():
	ma, mm = None, None
	random_ratios = load_pkl("/tmp/random.pkl")
	random_ratios = np.sort(random_ratios)
	print(len(random_ratios))
	ma = max(random_ratios)
	mm = min(random_ratios)
	y = np.arange(len(random_ratios)) / (len(random_ratios) - 1)
	# random_plot, = plt.plot(random_ratios, y, label="随机")

	ospf_ratios = load_pkl("/tmp/shortest.pkl")
	ospf_ratios = np.sort(ospf_ratios)
	ma = max(ma, max(ospf_ratios))
	mm = min(mm, min(ospf_ratios))

	y = np.arange(len(ospf_ratios)) / (len(ospf_ratios) - 1)
	ospf, = plt.plot(ospf_ratios, y, label="最短路")
	nn_ratios = load_pkl("/tmp/nn.pkl")
	nn_ratios = np.sort(nn_ratios)
	ma = max(ma, max(nn_ratios))
	mm = min(mm, min(nn_ratios))
	y = np.arange(len(nn_ratios)) / (len(nn_ratios) - 1)
	nn, = plt.plot(nn_ratios, y, label="监督学习")

	online_ratios = load_pkl("/tmp/online.pkl")
	online_ratios=np.sort(online_ratios)
	y = np.arange(len(online_ratios)) / (len(online_ratios) - 1)
	online, = plt.plot(online_ratios, y, label="online")

	plt.xlabel("g(u)")
	plt.ylabel("累计分布")
	plt.title("三种路由规划算法g(u)累计分布")
	plt.legend(handles=[online, ospf, nn])

	plt.savefig("/tmp/nn_result_cdf", dpi=300, bbox_inches='tight')
	plt.show()


def plot_single_utility(utilities, threshold):
	pass


def plot_utility():
	def reassemble(data, idxs):
		res = []
		for idx in idxs:
			res.append(data[idx])

		return res

	def scale(data, thres):
		return [d / thres for d in data]

	n_raw_case = 128 * 8

	ilp_utility = load_pkl("/tmp/ilp.utility.pkl")[:n_raw_case]
	ilp_utility = [u * 8 / 20 / (1.1 * 1e8) for u in ilp_utility]
	valid_idxs = []
	for idx in range(len(ilp_utility)):
		if ilp_utility[idx] < 1.2:
			valid_idxs.append(idx)

	print(len(valid_idxs))

	ospf_utility = load_pkl("/tmp/ospf.utility.pkl")[:n_raw_case]
	ospf_utility = [u * 8 / 20 / (1.1 * 1e8) for u in ospf_utility]
	ospf_utility = reassemble(ospf_utility, valid_idxs)
	ma = max(ospf_utility)
	ospf_utility = scale(ospf_utility, ma)

	with open("/tmp/ospf.utility.txt","w") as fp:
		for u in ospf_utility:
			fp.write("{}\n".format(u))
		fp.flush()


	figure = plt.gcf()
	figure.set_size_inches(18, 9)
	ospf_plot, = plt.plot(ospf_utility, label="最短路")
	ilp_utility = reassemble(ilp_utility, valid_idxs)
	ilp_utility = scale(ilp_utility, ma)
	ilp_plot, = plt.plot(ilp_utility, label="ILP最优")

	nn_utility = load_pkl("/tmp/nn.utility.pkl")[:n_raw_case]
	nn_utility = [u * 8 / 20 / (1.1 * 1e8) for u in nn_utility]

	nn_utility = reassemble(nn_utility, valid_idxs)
	nn_utility = scale(nn_utility, ma)
	nn_plot, = plt.plot(nn_utility, label="监督学习")
	with open("/tmp/nn.utility.txt","w") as fp:
		for u in ospf_utility:
			fp.write("{}\n".format(u))
		fp.flush()

	random_utility = load_pkl("/tmp/random.utility.pkl")[:n_raw_case]
	random_utility = [u * 8 / 20 / (1.1 * 1e8) for u in random_utility]
	random_utility = reassemble(random_utility, valid_idxs)
	random_utility = scale(random_utility, ma)
	random_plot, = plt.plot(random_utility, label="随机")

	online_utility = load_pkl("/tmp/online.utility.pkl")[:n_raw_case]
	online_utility = [u * 8 / 20 / (1.1 * 1e8) for u in online_utility]
	online_utility = reassemble(online_utility, valid_idxs)
	online_utility = scale(online_utility, ma)
	online_plot, = plt.plot(online_utility, label="online")

	with open("/tmp/online.utility.txt","w") as fp:
		for u in ospf_utility:
			fp.write("{}\n".format(u))
		fp.flush()

	plt.xlabel("测试用例")
	plt.ylabel("最大链路利用率")
	plt.title("四种路由规划算法利用率对比")
	# plt.legend(handles=[ilp_plot, nn_plot, ospf_plot, random_plot])
	plt.legend(handles=[ilp_plot, nn_plot, ospf_plot, online_plot])
	# plt.figure(figsize=(16,4))
	plt.savefig("/tmp/nn_test_ratio.png", dpi=300, bbox_inches='tight')
	plt.show()


# plt.savefig("/tmp/demo.utility.png")

def plot_nn_vs_ospf():
	def reassemble(data, idxs):
		res = []
		for idx in idxs:
			res.append(data[idx])

		return res

	def scale(data, thres):
		return [d / thres for d in data]

	n_raw_case = 128 * 8

	ilp_utility = load_pkl("/tmp/ilp.utility.pkl")[:n_raw_case]
	ilp_utility = [u * 8 / 20 / (1.1 * 1e8) for u in ilp_utility]
	valid_idxs = []
	for idx in range(len(ilp_utility)):
		if ilp_utility[idx] < 1.2:
			valid_idxs.append(idx)

	print(len(valid_idxs))

	ospf_utility = load_pkl("/tmp/ospf.utility.pkl")[:n_raw_case]
	ospf_utility = [u * 8 / 20 / (1.1 * 1e8) for u in ospf_utility]
	ospf_utility = reassemble(ospf_utility, valid_idxs)
	ma = max(ospf_utility)
	ospf_utility = scale(ospf_utility, ma)

	nn_utility = load_pkl("/tmp/nn.utility.pkl")[:n_raw_case]
	nn_utility = [u * 8 / 20 / (1.1 * 1e8) for u in nn_utility]

	nn_utility = reassemble(nn_utility, valid_idxs)
	nn_utility = scale(nn_utility, ma)

	ratios = []
	for idx in range(len(ospf_utility)):
		ratios.append((ospf_utility[idx] - nn_utility[idx]) / ospf_utility[idx])

	figure = plt.gcf()
	figure.set_size_inches(18, 9)

	plt.gca().set_yticklabels(['{:.0f}%'.format(x * 100)
	                           for x in plt.gca().get_yticks()])

	plt.xlabel("测试样例")
	plt.ylabel("优化百分比")
	plt.title("监督学习V.S.最短路")
	plt.plot(ratios, marker="o")
	# plt.plot(every_two)

	plt.savefig("/tmp/nn_test_mitigation.png", dpi=300, bbox_inches='tight')
	plt.show()


if __name__ == '__main__':
	# plot_nn_vs_ospf()
	plot_utility()
	# plot_cdf()
