import json
import os
import pickle
import random


from pathlib import Path
import loguru
import numpy as np

logger = loguru.logger
info=logger.info
debug=logger.debug
err=logger.error

def check_dir(dir_name):
    if not Path(dir_name).is_dir():
        raise FileNotFoundError

def check_file(fn):
    if not Path(fn).is_file():
        raise FileNotFoundError

def file_exsit(fn):
    return Path(fn).is_file()

def dir_exsit(fn):
    return Path(fn).is_dir()

def gaussion(mean:float,std_var:float,size=1):
    if size==1:
        return np.random.normal(mean,std_var)
    return np.random.normal(mean,std_var,size)

def exp(mean:float,size=1):
    if 1==size:
        return np.random.normal(mean)
    return np.random.normal(mean,size)
def uniform(low,up,size=1):
    if 1==size:
        return np.random.uniform(low,up)
    return np.random.uniform(low,up,size)


def load_pkl(filename):
    if Path(filename).is_file():
        data=None
        with open(filename,'rb') as file:
            data=pickle.load(file)
            file.close()
            return data
    raise FileNotFoundError

def save_pkl(filename,obj,overwrite=True):
    def write():
        with open(filename,'wb') as file:
            pickle.dump(obj,file)
            file.flush()
            file.close()

    if Path(filename).is_file() and overwrite:
        write()
        return

    write()

def load_json(filename):
    if Path(filename).is_file():
        with open(filename) as f:
            return json.load(f)
    raise FileNotFoundError

def save_json(filename,obj,overwrite=True):
    def write():
        with open(filename,'w',encoding="utf8") as file:
            json.dump(obj,file,indent=4)

    if Path(filename).is_file and overwrite:
        write()
        return
    write()

def is_digit(x:str)->bool:
    try:
        float(x)
        return True
    except:
        return False

def normalize(x):
	mi=min(x)
	ma=max(x)
	diff=ma-mi
	x=[(xx-mi)/diff for xx in x]
	return x


if __name__ == "__main__":
    pass
