def generate_ip(id_):
	id_ = int(id_) + 1
	if 1 <= id_ <= 254:
		return "10.0.0." + str(id_)
	if 255 <= id_ <= 255 * 254 + 253:
		return "10.0." + str(id_ // 254) + "." + str(id_ % 254)
	raise Exception("Cannot support id address given a too large id")


def generate_mac(id_):
	id_ = int(id_) + 1

	def base_16(num):
		res = []
		num = int(num)
		if num == 0:
			return "0"
		while num > 0:
			left = num % 16
			res.append(left if left < 10 else chr(ord('a') + (left - 10)))
			num //= 16
		res.reverse()
		return "".join(map(str, res))

	raw_str = base_16(id_)
	if len(raw_str) > 12:
		raise Exception("Invalid id")
	# reverse
	raw_str = raw_str[::-1]
	to_complete = 12 - len(raw_str)
	while to_complete > 0:
		raw_str += "0"
		to_complete -= 1
	mac_addr = ":".join([raw_str[i:i + 2] for i in range(0, len(raw_str), 2)])
	mac_addr = mac_addr[::-1]
	return mac_addr
