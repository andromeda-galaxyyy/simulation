import os 
import time 
import datetime
import subprocess




class status:
	#error
	resource_not_found=-1
	rest_resource_not_found=404
	parameter_invalid=-2
	rest_parameter_invalid=401

	#ok
	operation_done=1
	rest_operation_done=200

