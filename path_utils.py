from pathlib import  Path
import os.path
def get_prj_root():
	return os.path.abspath(os.curdir)
	# return Path(__file__).parent

if __name__ == '__main__':
    print(get_prj_root())