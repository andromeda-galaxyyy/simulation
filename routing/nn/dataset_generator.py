from keras.utils import Sequence
from typing import List, Dict, Tuple
from routing.instance import *
from utils.file_utils import *
import numpy as np
import tensorflow as tf


def mapper(instance: RoutingInstance) -> Tuple[List, List]:
	traffic_matrix = []
	labels = []
	traffic_matrix.extend(instance.video)
	labels.extend(instance.labels["video"])
	traffic_matrix.extend(instance.iot)
	labels.extend(instance.labels["iot"])
	traffic_matrix.extend(instance.voip)
	labels.extend(instance.labels["voip"])
	traffic_matrix.extend(instance.ar)
	labels.extend(instance.labels["ar"])

	return traffic_matrix, labels


class ILPGenerator(Sequence):
	def __init__(self, ilp_fns: List[str],
	             id_: int,
	             batch_size: int = 32,
	             n_nodes:int=66,
	             n_ksp:int=3,
	             n_flows:int=4):
		self.id = id_
		self.ilp_fns = ilp_fns
		self.batch_size = batch_size
		self.n_nodes=n_nodes
		self.n_ksp=n_ksp
		self.n_flows=n_flows

	def __len__(self):
		return 128 * len(self.ilp_fns) // self.batch_size

	def __getitem__(self, flow_idx):
		n_batch_per_file = 128 // self.batch_size
		file_idx= flow_idx // n_batch_per_file
		offset_in_file= flow_idx % n_batch_per_file
		fn=self.ilp_fns[file_idx]
		# debug(fn)
		batch_instances=load_pkl(fn)[self.batch_size*offset_in_file:(offset_in_file+1)*self.batch_size]

		batch_x=[]
		batch_y=[]

		n_nodes,n_ksp,n_flows=self.n_nodes,self.n_ksp,self.n_flows
		id_=self.id
		for instance in batch_instances:
			x,y=mapper(instance)
			batch_x.append(x)
			batch_y.append(y)

		batch_x=np.asarray(batch_x)
		batch_y=np.asarray(batch_y)

		batch_y=np.reshape(batch_y,(-1,n_flows,n_nodes*(n_nodes-1)))
		batch_y=batch_y[:,:,id_*(n_nodes-1):(id_+1)*(n_nodes-1)]
		output={}
		for flow_idx in range(self.n_flows):
			name="output{}".format(flow_idx)
			output[name]=batch_y[:,flow_idx,:]
		return batch_x,output



class ILPDataset(tf.data.Dataset):
	pass
