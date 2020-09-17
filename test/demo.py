from utils.file_utils import load_pkl,save_pkl
from collections import namedtuple


Point=namedtuple("Point",["x","y"])


if __name__ == '__main__':
	p=Point(11,12)
	save_pkl("/tmp/demo.pkl",p)
	p:Point=load_pkl("/tmp/demo.pkl")
	print(p.x+p.y)