import json
import numpy as np
from collections import Counter

import json
import torch
from path_utils import get_prj_root
from utils.log_utils import debug, info, err
from utils.file_utils import load_json
import os
from sockets.server import Server
from sockets.server import recvall2
import socketserver

model_static_dir = os.path.join(get_prj_root(), "routing/nn2.1/static")
models = {}
# readypaths = load_json(os.path.join(model_static_dir, "ready114paths.json"))
# indexofmodelin = load_json(os.path.join(model_static_dir, "linkpairofpath.json"))
ksps_tmp = load_json(os.path.join(get_prj_root(), "static/ksp.json"))["aksp"]
# debug(len(ksps_tmp))
# debug(len(ksps_tmp[0]))
ksps = []
for i in range(100):
	for j in range(100):
		if i == j: continue
		ksps.append(ksps_tmp[i][j])

assert len(ksps[0])==5
debug(ksps[0][4])
assert len(ksps) == 100 * 99


def outGoodPath(src1, src2, srcstep, dst1, dst2, dststep, allpathsanswer, matrixdata):
	answerindexofmodelin = [17, 19, 21, 23, 25, 27, 215, 217, 219, 221, 223, 225, 413, 415, 417,
	                        419, 421, 423, 39, 41,
	                        43, 45, 47, 49, 237, 239, 241, 243, 245, 247, 435, 437, 439, 441, 443,
	                        445, 655, 657, 659,
	                        661, 663, 665, 853, 855, 857, 859, 861, 863, 1051, 1053, 1055, 1057,
	                        1059, 1061, 677, 679,
	                        681, 683, 685, 687, 875, 877, 879, 881, 883, 885, 1073, 1075, 1077,
	                        1079, 1081, 1083, 1821,
	                        1823, 1825, 1827, 1829, 1831, 1920, 1922, 1924, 1926, 1928, 1930, 2019,
	                        2021, 2023, 2025,
	                        2027, 2029, 1807, 1808, 1809, 1810, 1811, 1812, 1813, 1814, 1906, 1907,
	                        1908, 1909, 1910,
	                        1911, 1912, 1913, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012]
	for i in range(1):
		for j in range(src1, src2 + 1, srcstep):
			for k in range(dst1, dst2 + 1, dststep):
				modelin = list()
				# strkey = str(j)+"->"+str(k)
				if matrixdata[i]["0"][j * 99 + k - 1] > 0:
					modelin.append(1)
				else:
					modelin.append(0)
				# for m in range(len(indexofmodelin[strkey])):
				#     indexofdata = str(indexofmodelin[strkey][m][0])+"->"+str(indexofmodelin[strkey][m][1])
				answerindexofmodelin2 = list()
				for m in range(len(answerindexofmodelin)):
					answerindexofmodelin2.append(allpathsanswer[answerindexofmodelin[m]])

				indexcount = Counter(answerindexofmodelin2)
				modelin.append(indexcount[2])
				modelin.append(indexcount[3])

				modelin = np.array(modelin)
				modelin = torch.tensor(modelin).float()
				key="{}-{}".format(j,k)
				if key not in models.keys():
					model=torch.load(os.path.join(model_static_dir,"model({}).pth".format(key)))
					models[key]=model
				model=models[key]

				# model = torch.load(
				# 	"/home/stack/code/dataforgoodpaths2/model(" + str(j) + "-" + str(k) + ").pth")
				answer = model(modelin).data
				answer = np.array(answer)
				answer = answer.tolist()
				answer.reverse()
				pathindex = 0
				for n in range(3):
					if answer[n] > 0.5:
						pathindex = pathindex + (2 ** n)
				if pathindex > 4:
					pathindex = 0
				allpathsanswer[j * 99 + k - 1] = pathindex

	return allpathsanswer  # ,linksratedict


def out114Goodpaths(matrixdatadict):
	matrixdata = list()
	matrixdata.append(matrixdatadict)

	allpathsanswer = [0] * 9900

	allpathsanswer = outGoodPath(0, 4, 2, 18, 28, 2, allpathsanswer, matrixdata)
	allpathsanswer = outGoodPath(0, 4, 2, 40, 50, 2, allpathsanswer, matrixdata)
	allpathsanswer = outGoodPath(6, 10, 2, 62, 72, 2, allpathsanswer, matrixdata)
	allpathsanswer = outGoodPath(6, 10, 2, 84, 94, 2, allpathsanswer, matrixdata)
	allpathsanswer = outGoodPath(18, 20, 1, 40, 50, 2, allpathsanswer, matrixdata)
	allpathsanswer = outGoodPath(18, 20, 1, 26, 33, 1, allpathsanswer, matrixdata)

	return allpathsanswer


class handler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req = recvall2(self.request)
		req = json.loads(req)
		# rate = req["rate"]
		matrix = req["matrix"]
		# debug(req)
		allpathsanswer = out114Goodpaths(matrix)
		# print(allpathsanswer[17], allpathsanswer[19], allpathsanswer[21], allpathsanswer[23],
		#       allpathsanswer[25], allpathsanswer[27], allpathsanswer[215], allpathsanswer[217],
		#       allpathsanswer[219], allpathsanswer[221], allpathsanswer[1807], allpathsanswer[1808],
		#       allpathsanswer[1809], allpathsanswer[1810], allpathsanswer[1811])
		debug(len(allpathsanswer))
		paths = []
		# for demand_idx in range()
		for demand_idx,path_idx in enumerate(allpathsanswer):
			paths.append(ksps[demand_idx][path_idx])
		res = {
			"res1": paths
		}
		self.request.sendall(bytes(json.dumps(res) + "*", "ascii"))

if __name__ == '__main__':
	with open(os.path.join(get_prj_root(),"routing/nn2.1//matrixtest.json"), encoding="utf-8") as f4:
		matrixdatadict = json.load(f4)

	allpathsanswer = out114Goodpaths(matrixdatadict)
	# debug(len(allpathsanswer))
	port=1055
	server=Server(port,handler)
	server.start()

