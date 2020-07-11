import os
from pathlib import Path
from utils.log_utils import debug

if __name__ == '__main__':
	fn="/tmp/pkts/video/VIDEO_Vimeo_Gateway.pkts"
	new_fn="/tmp/pkts/video/VIDEO_Vimeo_Gateway_trimmed.pkts"
	lines=None
	with open(fn,"r") as fp:
		lines=fp.readlines()
		fp.close()
	debug("#lines: {}".format(len(lines)))

	length=len(lines)

	lines=lines[int(0.1*length):int(0.9*length)]
	new_len=len(lines)
	debug("#lines after trimmed: {}".format(new_len))
	with open(new_fn,"w") as fp:
		for l in lines:
			fp.write("{}".format(l))
		fp.flush()
		fp.close()



