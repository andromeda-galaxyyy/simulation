import random
from typing import List, Any


def shuffle_list(contents: List[Any]) -> List[Any]:
	'''

	:param contents: list of anything
	:return: shuffled contents
	'''
	random.shuffle(contents)
	return contents
