import json
import numpy as np
import torch
from path_utils import get_prj_root
from utils.log_utils import debug, info, err
from utils.file_utils import load_json
import os
from sockets.server import Server
from sockets.server import recvall2
import socketserver

model_static_dir = os.path.join(get_prj_root(), "routing/nn2/static")
models = {}
readypaths = load_json(os.path.join(model_static_dir, "ready114paths.json"))
indexofmodelin = load_json(os.path.join(model_static_dir, "linkpairofpath.json"))
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


def outGoodPath(src1, src2, srcstep, dst1, dst2, dststep, linksratedict, allpathsanswer,
                matrixdata):
	# with open("/home/stack/code/dataforgoodpaths/ready114paths.json", encoding="utf-8") as f5:
	#     readypaths = json.load(f5)
	#
	# with open("/home/stack/code/dataforgoodpaths/linkpairofpath.json", encoding="utf-8") as f3:
	#     indexofmodelin = json.load(f3)

	for i in range(1):
		for j in range(src1, src2 + 1, srcstep):
			for k in range(dst1, dst2 + 1, dststep):
				modelin = list()
				strkey = str(j) + "->" + str(k)
				for m in range(len(indexofmodelin[strkey])):
					indexofdata = str(indexofmodelin[strkey][m][0]) + "->" + str(
						indexofmodelin[strkey][m][1])
					modelin.append(linksratedict[i][indexofdata])
				modelin = np.array(modelin)
				modelin = torch.tensor(modelin).float()
				model_key = "{}-{}".format(j, k)
				model_fn = "model({}).pth".format(model_key)
				model_fn = os.path.join(model_static_dir, model_fn)
				if model_key in models.keys():
					model = models[model_key]
				else:
					model = torch.load(model_fn)
					# model = torch.load(
					# 	"/home/stack/code/dataforgoodpaths/model(" + str(j) + "-" + str(
					# 		k) + ").pth")
					models[model_key] = model
				answer = model(modelin).data
				answer = np.array(answer)
				answer = answer.tolist()
				pathindex = 0
				for n in range(2, -1, -1):
					if answer[n] > 0.5:
						pathindex = pathindex + (2 ** n)
				if pathindex > 4:
					pathindex = 0
				allpathsanswer[j * 99 + k - 1] = pathindex
				goodpath = readypaths[str(j) + "->" + str(k)][pathindex]
				for p in range(len(goodpath) - 1):
					strkey3 = str(goodpath[p]) + "->" + str(goodpath[p + 1])
					linksratedict[i][strkey3] = linksratedict[i][strkey3] + matrixdata[i]["0"][
						j * 99 + k - 1]

	return allpathsanswer, linksratedict


thepathsIneed = [load_json(os.path.join(model_static_dir, "alllinksnopeat.json"))]


def out114Goodpaths(ratedatadict, matrixdatadict):
	matrixdata = list()
	matrixdata.append(matrixdatadict)

	ratedatayuan = list()
	ratedatayuan.append(ratedatadict)

	# thepathsIneed = list()
	# with open("/home/stack/code/dataforgoodpaths/alllinksnopeat.json", encoding="utf-8") as f1:
	# 	thepathsIneed.append(json.load(f1))

	linksratedict = list()
	for i in range(len(ratedatayuan)):
		linksratedictmiddle = dict()
		for j in range(len(thepathsIneed[0]["allpathspair"])):
			strkey = str(thepathsIneed[0]["allpathspair"][j][0]) + "->" + str(
				thepathsIneed[0]["allpathspair"][j][1])
			strkey1 = str(thepathsIneed[0]["allpathspair"][j][1]) + "->" + str(
				thepathsIneed[0]["allpathspair"][j][0])

			if (ratedatayuan[i][strkey] > 5 or ratedatayuan[i][strkey1] > 5):
				ratedatayuan[i][strkey] = 1
				ratedatayuan[i][strkey1] = ratedatayuan[i][strkey]
			linksratedictmiddle.update({strkey: ratedatayuan[i][strkey] + ratedatayuan[i][strkey1]})
		linksratedict.append(linksratedictmiddle)

	allpathsanswer = [0] * 9900

	allpathsanswer, linksratedict = outGoodPath(0, 4, 2, 18, 28, 2, linksratedict, allpathsanswer,
	                                            matrixdata)
	allpathsanswer, linksratedict = outGoodPath(0, 4, 2, 40, 50, 2, linksratedict, allpathsanswer,
	                                            matrixdata)
	allpathsanswer, linksratedict = outGoodPath(6, 10, 2, 62, 72, 2, linksratedict, allpathsanswer,
	                                            matrixdata)
	allpathsanswer, linksratedict = outGoodPath(6, 10, 2, 84, 94, 2, linksratedict, allpathsanswer,
	                                            matrixdata)
	allpathsanswer, linksratedict = outGoodPath(18, 20, 1, 40, 50, 2, linksratedict, allpathsanswer,
	                                            matrixdata)
	allpathsanswer, linksratedict = outGoodPath(18, 20, 1, 26, 33, 1, linksratedict, allpathsanswer,
	                                            matrixdata)

	return allpathsanswer


class handler(socketserver.BaseRequestHandler):
	def handle(self) -> None:
		req = recvall2(self.request)
		req = json.loads(req)
		rate = req["rate"]
		matrix = req["matrix"]
		debug(req)
		allpathsanswer = out114Goodpaths(rate, matrix)
		print(allpathsanswer[17], allpathsanswer[19], allpathsanswer[21], allpathsanswer[23],
		      allpathsanswer[25], allpathsanswer[27], allpathsanswer[215], allpathsanswer[217],
		      allpathsanswer[219], allpathsanswer[221], allpathsanswer[1807], allpathsanswer[1808],
		      allpathsanswer[1809], allpathsanswer[1810], allpathsanswer[1811])
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
	# with open("/home/stack/code/dataforgoodpaths/ratetest.json", encoding="utf-8") as f2:
	# 	ratedatedict = json.load(f2)
	#
	# with open("/home/stack/code/dataforgoodpaths/matrixtest.json", encoding="utf-8") as f4:
	# 	matrixdatadict = json.load(f4)
	'''
	{
		"rate":{},
		"matrix":{}
	}*
	'''
	ratedatedict = load_json(os.path.join(model_static_dir, "ratetest.json"))
	matrixdatadict = load_json(os.path.join(model_static_dir, "matrixtest.json"))

	allpathsanswer = out114Goodpaths(ratedatedict, matrixdatadict)
	debug(allpathsanswer[0])
	assert len(allpathsanswer)==100*99
	print(allpathsanswer[17], allpathsanswer[19], allpathsanswer[21], allpathsanswer[23],
	      allpathsanswer[25], allpathsanswer[27], allpathsanswer[215], allpathsanswer[217],
	      allpathsanswer[219], allpathsanswer[221], allpathsanswer[1807], allpathsanswer[1808],
	      allpathsanswer[1809], allpathsanswer[1810], allpathsanswer[1811])

	server=Server(1055,handler)
	server.start()
