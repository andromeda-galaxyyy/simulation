from utils.log_utils import info, debug, err


class DummyModel:
	def __init__(self):
		pass

	def __call__(self, *args, **kwargs):
		return 4
