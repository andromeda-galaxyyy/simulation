import json
import pickle
import os


def check_file(fn):
    if not os.path.isfile(fn):
        raise IOError

def load_pkl(filename):
    if os.path.isfile(filename):
        data=None
        with open(filename,'rb') as file:
            data=pickle.load(file)
            file.close()
            return data
    raise IOError

def save_pkl(filename,obj,overwrite=True):
    def write():
        with open(filename,'wb') as file:
            pickle.dump(obj,file)
            file.flush()
            file.close()

    if os.path.isfile(filename) and overwrite:
        write()
        return

    write()

def load_json(filename):
    if os.path.isfile(filename):
        with open(filename) as f:
            return json.load(f)
    raise IOError

def save_json(filename,obj,overwrite=True):
    def write():
        with open(filename,'w') as file:
            json.dump(obj,file,indent=4)

    if os.path.isfile(filename) and overwrite:
        write()
        return
    write()

def is_digit(x):
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

def get_prj_root():
    return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    pass
