from sklearn.tree import DecisionTreeClassifier
from path_utils import get_prj_root
from pathlib import Path
import os
from utils.common_utils import save_pkl,load_pkl

root_dir=get_prj_root()
model_dir=os.path.join(root_dir,"models")

class Classifier:
	# def __init__(self,fn_name=None):
	# 	self.model=None
	# 	if fn_name is not None:
	# 		self.load_model(fn_name)


	def fit(self,data):
		raise NotImplementedError

	def predict(self,features):
		raise NotImplementedError

	def save_model(self,fn_name):
		raise NotImplementedError

	def load_model(self,fn_name):
		raise NotImplementedError

class DT(Classifier):
	def __init__(self):
		super(DT, self).__init__()
		self.model:DecisionTreeClassifier=DecisionTreeClassifier()


	def fit(self,data):
		assert len(data)==2
		features=data[0]
		y=data[1]
		assert len(features)==len(y)
		self.model.fit(features,y)

	def predict(self,features):
		return self.model.predict(features)

	def save_model(self,fn_name):
		if self.model is None:return
		fn_name=os.path.join(model_dir,fn_name)
		save_pkl(fn_name,self.model)


	def load_model(self,fn_name):
		fn_name=os.path.join(model_dir,fn_name)
		self.model:DecisionTreeClassifier=load_pkl(fn_name)




if __name__ == '__main__':
    from sklearn.datasets import load_iris
    x,y=load_iris(return_X_y=True)
    model=DT()
    model.fit((x,y))
    # model.save_model("test.pkl")
    model.load_model("test.pkl")
