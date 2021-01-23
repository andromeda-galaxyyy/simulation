import json
from os import link
import time
import copy
import socket
import sys
import copy
import os
from path_utils import get_prj_root
from utils.log_utils import debug, info, err


class table:
	def __init__(self, links, path, switches, monitor, vlan):
		self.Links = copy.deepcopy(links)
		self.link_flag = dict()  ### 记录待测链路是否进行了多播返回操作
		self.n_switches = switches
		self.monitor = monitor
		self.sip = "172.18.0.1"
		self.dip = "172.18.0.2"
		self.multi_flag = {}
		self.paths = path
		self.multi_p = []
		self.multi_n = {}
		self.json_dict = {}
		self.vlan_id = vlan
		self.flow_num=0
		# self.act={"action 1":{},"action 2":{}}

	################################################
	# 多播的交换机id,以及多播下一跳
	def compute_muiti(self, l):
		multi_nodes = {}
		multi_list = []
		# x=0
		for i in range(len(l)):  ## 对于每一条path来说
			for j in range(i + 1, len(l)):  ###对于其他路径来说
				for n in range(min(len(l[i]), len(l[j]))):  # 获得两条路径的最短长度
					if l[i][n] == l[j][n]:
						continue
					if l[i][:n] not in multi_list:
						multi_list.append(l[i][:n])
						x = len(multi_list)
						multi_nodes[x] = []
						multi_nodes[x].append(l[i][n])
						multi_nodes[x].append(l[j][n])
					else:
						index = multi_list.index(l[i][:n]) + 1
						if l[i][n] not in multi_nodes[index]:
							# print(l[i][:n], "already in multi_p", "add:", l[i][n])
							multi_nodes[index].append(l[i][n])
						elif l[j][n] not in multi_nodes[index]:
							# print(l[i][:n], "already in multi_p", "add:", l[j][n])
							multi_nodes[index].append(l[j][n])
					break
		return multi_list, multi_nodes

	#############################################
	# 结果汇总
	def make_res(self):
		# self.multi_p, self.multi_n = self.compute_muiti(self.paths)
		# self.is_probelink()
		# self.multi_p=[[0, 1], [0, 1, 2, 3], [0, 1, 2], [0, 1, 6], [0, 1, 2, 4], [0, 1, 2, 5], [0, 1, 8],
		#  [0, 1, 6, 7], [0, 1, 9], [0, 1, 8, 10], [0, 1, 12], [0, 1, 13], [0, 1, 13, 14],
		#  [0, 1, 13, 15], [0, 1, 13, 17], [0, 1, 13, 18], [0, 1, 2, 35], [0, 1, 8, 37],
		#  [0, 1, 6, 58], [0, 1, 9, 59], [0, 1, 12, 61], [0, 1, 79], [0, 1, 79, 80], [0, 1, 79, 81],
		#  [0, 1, 79, 83], [0, 1, 79, 84], [0, 1, 13, 14, 16], [0, 1, 2, 5, 36], [0, 1, 8, 37, 38],
		#  [0, 1, 2, 35, 39], [0, 1, 2, 35, 40], [0, 1, 2, 3, 57], [0, 1, 6, 58, 60],
		#  [0, 1, 6, 58, 62], [0, 1, 79, 80, 82], [0, 1, 6, 11]]
		self.multi_p = [[0, 1], [0, 1, 2, 3], [0, 1, 2], [0, 1, 6], [0, 1, 2, 4], [0, 1, 2, 5],
		           [0, 1, 8], [0, 1, 6, 7], [0, 1, 9], [0, 1, 8, 10], [0, 1, 12], [0, 1, 13],
		           [0, 1, 13, 14], [0, 1, 13, 15], [0, 1, 13, 17], [0, 1, 13, 18], [0, 1, 2, 35],
		           [0, 1, 8, 37], [0, 1, 6, 58], [0, 1, 9, 59], [0, 1, 12, 61], [0, 1, 79],
		           [0, 1, 79, 80], [0, 1, 79, 81], [0, 1, 79, 83], [0, 1, 79, 84],
		           [0, 1, 13, 14, 16], [0, 1, 2, 5, 36], [0, 1, 8, 37, 38], [0, 1, 2, 35, 39],
		           [0, 1, 2, 35, 40], [0, 1, 2, 3, 57], [0, 1, 6, 58, 60], [0, 1, 6, 58, 62],
		           [0, 1, 79, 80, 82], [0, 1, 6, 11]]
		self.multi_n = {1: [2, 6, 8, 9, 12, 13, 79, 0], 2: [4, 7, 57, 2], 3: [3, 4, 5, 35, 1],
		 4: [3, 5, 7, 11, 58, 1], 5: [5, 7, 14, 80, 2], 6: [7, 11, 36, 2], 7: [7, 9, 12, 10, 37, 1],
		 8: [15, 81, 6], 9: [10, 12, 59, 1], 10: [11, 17, 83, 8], 11: [10, 11, 61, 1],
		 12: [19, 21, 23, 25, 27, 29, 31, 33, 14, 15, 17, 18, 1],
		 13: [15, 18, 20, 22, 24, 26, 28, 30, 32, 34, 16, 13],
		 14: [16, 17, 19, 21, 23, 25, 27, 29, 31, 33, 13],
		 15: [16, 18, 19, 21, 23, 25, 27, 29, 31, 33, 13],
		 16: [16, 20, 22, 24, 26, 28, 30, 32, 34, 13],
		 17: [36, 37, 41, 43, 45, 47, 49, 51, 53, 55, 39, 40, 2],
		 18: [36, 39, 41, 43, 45, 47, 49, 51, 53, 55, 38, 8],
		 19: [57, 59, 64, 66, 68, 70, 72, 74, 76, 78, 60, 62, 6],
		 20: [57, 60, 61, 63, 65, 67, 69, 71, 73, 75, 77, 9],
		 21: [57, 60, 62, 63, 65, 67, 69, 71, 73, 75, 77, 12],
		 22: [85, 87, 89, 91, 93, 95, 97, 99, 80, 81, 83, 84, 1],
		 23: [81, 84, 86, 88, 90, 92, 94, 96, 98, 100, 82, 79],
		 24: [82, 83, 85, 87, 89, 91, 93, 95, 97, 99, 79],
		 25: [82, 84, 85, 87, 89, 91, 93, 95, 97, 99, 79],
		 26: [82, 86, 88, 90, 92, 94, 96, 98, 100, 79], 27: [20, 22, 24, 26, 28, 30, 32, 34, 14],
		 28: [38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 5],
		 29: [39, 40, 42, 44, 46, 48, 50, 52, 54, 56, 37],
		 30: [40, 41, 43, 45, 47, 49, 51, 53, 55, 35], 31: [42, 44, 46, 48, 50, 52, 54, 56, 35],
		 32: [62, 63, 65, 67, 69, 71, 73, 75, 77, 3], 33: [62, 64, 66, 68, 70, 72, 74, 76, 78, 58],
		 34: [64, 66, 68, 70, 72, 74, 76, 78, 58], 35: [86, 88, 90, 92, 94, 96, 98, 100, 80],
		 36: [6, 39]}

		# self.multi_n={1: [2, 6, 8, 9, 12, 13, 79, 0], 2: [4, 7, 57, 2], 3: [3, 4, 5, 35, 1],
		#  4: [3, 5, 7, 11, 58, 1], 5: [5, 7, 14, 80, 2], 6: [7, 11, 36, 2], 7: [7, 9, 12, 10, 37, 1],
		#  8: [15, 81, 6], 9: [10, 12, 59, 1], 10: [11, 17, 83, 8], 11: [10, 11, 61],
		#  12: [19, 21, 23, 25, 27, 29, 31, 33, 14, 15, 17, 18, 1],
		#  13: [15, 18, 20, 22, 24, 26, 28, 30, 32, 34, 16, 13],
		#  14: [16, 17, 19, 21, 23, 25, 27, 29, 31, 33, 13],
		#  15: [16, 18, 19, 21, 23, 25, 27, 29, 31, 33, 13],
		#  16: [16, 20, 22, 24, 26, 28, 30, 32, 34, 13],
		#  17: [36, 37, 41, 43, 45, 47, 49, 51, 53, 55, 39, 40, 2],
		#  18: [36, 39, 41, 43, 45, 47, 49, 51, 53, 55, 38, 8],
		#  19: [57, 59, 64, 66, 68, 70, 72, 74, 76, 78, 60, 62, 6],
		#  20: [57, 60, 61, 63, 65, 67, 69, 71, 73, 75, 77, 9],
		#  21: [57, 60, 62, 63, 65, 67, 69, 71, 73, 75, 77, 12],
		#  22: [85, 87, 89, 91, 93, 95, 97, 99, 80, 81, 83, 84, 1],
		#  23: [81, 84, 86, 88, 90, 92, 94, 96, 98, 100, 82, 79],
		#  24: [82, 83, 85, 87, 89, 91, 93, 95, 97, 99, 79],
		#  25: [82, 84, 85, 87, 89, 91, 93, 95, 97, 99, 79],
		#  26: [82, 86, 88, 90, 92, 94, 96, 98, 100, 79], 27: [20, 22, 24, 26, 28, 30, 32, 34, 14],
		#  28: [38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 5],
		#  29: [39, 40, 42, 44, 46, 48, 50, 52, 54, 56, 37],
		#  30: [40, 41, 43, 45, 47, 49, 51, 53, 55, 35], 31: [42, 44, 46, 48, 50, 52, 54, 56],
		#  32: [62, 63, 65, 67, 69, 71, 73, 75, 77, 3], 33: [62, 64, 66, 68, 70, 72, 74, 76, 78, 58],
		#  34: [64, 66, 68, 70, 72, 74, 76, 78, 58], 35: [86, 88, 90, 92, 94, 96, 98, 100, 80],36: [6, 39]}
		print("multi_p", self.multi_p, '\n', "multi_n", self.multi_n)
		self.IPV4forward()
		self.last_forward()
		self.multi_forward()
		info(self.json_dict)
		info(len(self.json_dict['1']))

		with open(os.path.join(get_prj_root(), "static/telemetry.flow.json"), 'w') as f:
			data = json.dumps(self.json_dict)
			# try:
			#     s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
			#     s.connect(("localhost",6666))
			# except socket.error as msg:
			#     print(msg)
			#     sys.exit(1)
			# # print(len(data))
			# data_b=str.encode(data)
			# data_b+="*"
			# s.sendall(data_b)
			json.dump(self.json_dict, f)
			# json.dump(self.edges_port,f)
		return self.json_dict

	###########################################
	# 判断是否是待测链路    探测链路两端节点都要返回数据包（只处理了一端节点 另一端节点未处理#）
	# def probeLink(self):
	#     for i in self.Links:
	def is_probelink(self):
		links = self.Links
		for x in links:
			self.link_flag[x] = 0
		for path in self.paths:
			p_list = []
			for i in range(len(path) - 1):  ##判断待测链路节点是否已经是多播节点 不是则新建多播组 是则加入多播组,尾节点会直接返回
				flag = 0
				p_list.append(path[i])

				if (path[i], path[i + 1]) in self.Links:
					# print(self.Links)
					# print(self.Links)
					# print(path[i], path[i + 1],11111)
					# print(self.link_flag)
					flag = 1
				elif (path[i + 1], path[i]) in self.Links:
					# print(path[i+1], path[i],22222222)
					flag = 2
				if flag == 1 and self.link_flag[(path[i], path[i + 1])] == 0:
					##处理节点1
					self.add_multi(p_list, path, i)
					##处理节点2
					if path[i + 1] == path[-1]:  # 如果尾节点是路径最后一跳 则不进行尾节点的操作
						continue
					p_next_list = copy.deepcopy(p_list)
					p_next_list.append(path[i + 1])
					self.add_multi(p_next_list, path, i + 1)
					# p_list.pop()
					self.link_flag[(path[i], path[i + 1])] = 1
				elif flag == 2 and self.link_flag[(path[i + 1], path[i])] == 0:
					# print("flag==2")
					# p_list.append(path[i])
					self.add_multi(p_list, path, i)
					##处理节点2
					if path[i + 1] == path[-1]:  # 如果尾节点是路径最后一跳 则不进行尾节点的操作
						continue
					p_next_list = copy.deepcopy(p_list)
					p_next_list.append(path[i + 1])
					# time.sleep(1)
					self.add_multi(p_next_list, path, i + 1)
					# p_list.pop()
					self.link_flag[(path[i + 1], path[i])] = 1

	def add_multi(self, p_list, path, i):  #####path[i] 不仅返回给上一跳 还要发送到下一跳
		if p_list in self.multi_p:
			index_p = self.multi_p.index(p_list) + 1
			if path[i + 1] not in self.multi_n[index_p]:
				self.multi_n[index_p].append(path[i + 1])
				# print(p_list, "is in multi_p,在{}处添加多播节点i+1=>{}".format(index_p,path[i+1]))
			if path[i - 1] not in self.multi_n[index_p]:
				self.multi_n[index_p].append(path[i - 1])
				# print(p_list, "is in multi_p,在{}处添加多播节点i-1=>{}".format(index_p, path[i - 1]))
		else:
			self.multi_p.append(p_list)
			n_list = [path[i - 1], path[i + 1]]
			self.multi_n[len(self.multi_p)] = n_list
			# print(p_list, "is not in multi_p,添加多播节点=>{}".format(n_list),"multi_p 长度：",len(self.multi_p))
			# print(self.multi_p)

	###########################################
	# 中间转发节点
	def IPV4forward(self):
		for path in self.paths:
			# print("path ",path)
			p_list = [0]
			last_node = path[-1]
			for i in range(1, len(path) - 1):
				# print("i:",i)
				multi_flag = 1
				p_list.append(path[i])
				if p_list in self.multi_p:
					n_index = self.multi_p.index(p_list) + 1
					if path[i + 1] not in self.multi_n[n_index]:
						multi_flag = 0
				elif p_list not in self.multi_p:
					multi_flag = 0
				if multi_flag == 0:
					# print((path[i],path[i+1]),'=>',self.get_port(path[i], path[i+1]))
					temp = {}
					outport = []
					outport.append(path[i + 1])
					temp['outport'] = outport
					act = {}
					act['action1'] = temp
					# act['action 2']={}
					table = {}
					self.flow_num += 1
					table['172.18.0.1,{}'.format(path[i - 1])] = act
					if '{}'.format(path[i]) not in self.json_dict.keys():
						self.json_dict['{}'.format(path[i])] = table
					elif '172.18.0.1,{}'.format(path[i - 1]) in self.json_dict[
						'{}'.format(path[i])].keys():
						self.json_dict['{}'.format(path[i])][
							'172.18.0.1,{}'.format(path[i - 1])]['action1']['outport'] = outport
					elif '172.18.0.1,{}'.format(path[i - 1]) not in self.json_dict[
						'{}'.format(path[i])].keys():
						self.json_dict['{}'.format(path[i])][
							'172.18.0.1,{}'.format(path[i - 1])] = act

				# 返回数据包的处理
				# if path[i]!=last_node:  #中间节点的返回处理       (src,inport)  action1: outport:
				outport = []
				outport.append(path[i - 1])
				for j in range(i + 1, len(path)):
					temp = {}
					act = {}
					temp['outport'] = outport
					act['action1'] = temp
					# self.act['action 2']={}
					table = {}
					self.flow_num +=1
					table['172.18.1.{},{}'.format(path[j], path[i + 1])] = act
					if '{}'.format(path[i]) not in self.json_dict.keys():
						# print('{}'.format(path[i]),"not in elf.json_dict.keys()","self.json_dict['{}'] ={}".format(path[i],table))
						self.json_dict['{}'.format(path[i])] = table
					elif '172.18.1.{},{}'.format(path[j], path[i + 1]) in self.json_dict[
						'{}'.format(path[i])].keys():
						# print('{}'.format(path[i]),('10.0.1.{},{}'.format(path[j],self.get_port(path[i], path[i+1]))),"in json list","['action1']['outport'] = ",self.get_port(path[i], path[i-1]))
						self.json_dict['{}'.format(path[i])][
							'172.18.1.{},{}'.format(path[j], path[i + 1])]['action1'][
							'outport'] = outport
					elif ('172.18.1.{}'.format(path[j]), path[i + 1]) not in self.json_dict[
						'{}'.format(path[i])].keys():
						# print('{}'.format(path[i]),('10.0.1.{}'.format(path[j]), self.get_port(path[i], path[i + 1])), "not in json list",
						#       '10.0.1.{},{}'.format(path[j], self.get_port(path[i], path[i + 1])),"=",act)
						self.json_dict['{}'.format(path[i])]['172.18.1.{},{}'.format(
							path[j], path[i + 1])] = act

	###########################################
	# 路径最后一跳 返回探测包  修改srcip 、 dstip
	def last_forward(self):
		for path in self.paths:
			####json
			temp = {}
			# temp['outport']=self.get_port(path[- 1],path[- 2])
			temp['src'] = '172.18.1.{}'.format(path[-1])
			temp['dst'] = '172.18.0.1'
			temp["vlan"] = self.vlan_id[(path[-1], path[-2])]
			# temp['vlan']=self.get_port(path[- 1],path[- 2])
			act = {}
			act['action2'] = temp
			table = {}
			self.flow_num += 1
			table['172.18.0.1,{}'.format(path[- 2])] = act
			if '{}'.format(path[-1]) not in self.json_dict.keys():
				self.json_dict['{}'.format(path[-1])] = table
			elif '172.18.0.1,{}'.format(path[- 2]) in self.json_dict[
				'{}'.format(path[-1])].keys():
				self.json_dict['{}'.format(path[-1])][
					'172.18.0.1,{}'.format(path[- 2])]['action2'] = temp
			elif '172.18.0.1,{}'.format(path[- 2]) not in self.json_dict[
				'{}'.format(path[-1])].keys():
				self.json_dict['{}'.format(path[-1])][
					'172.18.0.1,{}'.format(path[- 2])] = act

	###########################################
	#####处理多播转发 多播组与端口的绑定以及多播后srcip、dstip的修改
	def multi_forward(self):
		for i in self.multi_n.keys():
			# egress_rid=0
			n_list = self.multi_p[i - 1]
			# print("n_list:",n_list,"multi_n:",self.multi_n[i])
			outport = []
			for m in self.multi_n[i]:
				if m != n_list[-2]:
					print("{} add next node {}".format(n_list[-1],m))
					outport.append(m)
				else:
					# print(n_list,"=>",m,"修改src、dst","outport=",self.get_port(n_list[-1],n_list[-2]))
					temp = {}
					self.flow_num += 1
					# temp['outport'] = self.get_port(n_list[-1],n_list[-2])
					temp['src'] = '172.18.1.{}'.format(n_list[-1])
					temp['dst'] = '172.18.0.1'
					temp['vlan'] = self.vlan_id[(n_list[-1], n_list[-2])]
					# temp['vlan'] = self.get_port(n_list[-1],n_list[-2])
					act = {}
					act['action2'] = temp
					table = {}
					table['172.18.0.1,{}'.format(n_list[-2])] = act
					if '{}'.format(n_list[-1]) not in self.json_dict.keys():
						self.json_dict['{}'.format(n_list[-1])] = table
					elif '172.18.0.1,{}'.format(n_list[-2]) in self.json_dict[
						'{}'.format(n_list[-1])].keys():
						self.json_dict['{}'.format(n_list[-1])][
							'172.18.0.1,{}'.format(n_list[-2])]['action2'] = temp
					elif '172.18.0.1,{}'.format(n_list[-2]) not in self.json_dict[
						'{}'.format(n_list[-1])].keys():
						self.json_dict['{}'.format(n_list[-1])][
							'172.18.0.1,{}'.format(n_list[-2])] = act
			# print("outport:",outport)
			temp = {}
			temp['outport'] = outport
			act = {}
			act['action1'] = temp
			table = {}
			table['172.18.0.1,{}'.format(n_list[-2])] = act
			self.flow_num += 1
			if '{}'.format(n_list[-1]) not in self.json_dict.keys():
				self.json_dict['{}'.format(n_list[-1])] = table
			elif '172.18.0.1,{}'.format(n_list[-2]) in self.json_dict[
				'{}'.format(n_list[-1])].keys():
				self.json_dict['{}'.format(n_list[-1])][
					'172.18.0.1,{}'.format(n_list[-2])]['action1'] = temp
			elif '172.18.0.1,{}'.format(n_list[-2]) not in self.json_dict[
				'{}'.format(n_list[-1])].keys():
				self.json_dict['{}'.format(n_list[-1])][
					'172.18.0.1,{}'.format(n_list[-2])] = act


if __name__ == '__main__':
	import os
	from path_utils import get_prj_root
	from utils.file_utils import load_json, load_pkl, save_pkl

	links = []
	topo = load_json(os.path.join(get_prj_root(), "static/topo.json"))["topo"]
	for i in range(100):
		for j in range(100):
			# if i>=j:continue
			if -1 not in topo[i][j]:
				links.append((i, j))
	# assert len(links)==
	save_pkl(os.path.join(get_prj_root(), "static/telemetry.links.pkl"), links)
	# links=load_pkl(os.path.join(get_prj_root(),"static/telemetry.links.pkl"))
	link_to_vlan = load_pkl(os.path.join(get_prj_root(), "static/telemetry.link_to_vlan.pkl"))

	# links=[(2,3),(1,6),(3,4)]
	# paths=[[0,5, 2, 1], [0,5, 6, 1], [0,5, 2, 3], [0,5, 3, 4], [0,5, 7, 4], [0,5, 6, 7]]
	# paths=[[23, 12, 13, 14, 15],[23, 12, 22],[23, 24, 13, 14, 15, 16]]
	# links=[(23,12),(16,15),(14,15)]
	paths = load_json(os.path.join(get_prj_root(), "static/telemetry.paths.json"))["paths"]
	# # print(len(paths))
	t = table(links, paths, 100, 1, link_to_vlan)
	t.make_res()
	print(t.flow_num)
	print("done!")
