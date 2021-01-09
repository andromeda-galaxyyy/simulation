import numpy as np


def gaussion(mean, std):
	return np.random.normal(mean, std)

def normalize(x):
	mi=min(x)
	ma=max(x)
	diff=ma-mi
	x=[(xx-mi)/diff for xx in x]
	return x

def uniform(low, up):
	return np.random.uniform(low, up)


def is_digit(x:str)->bool:
    try:
        float(x)
        return True
    except:
        return False