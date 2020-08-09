
inter=413696.0

if __name__ == '__main__':
	first_line="{} 1000 TCP 0 -1 0".format(inter)
	line="{} 1000 TCP 0 {} 0".format(inter,inter)
	last_line="-1 1000 TCP 0 {} 1".format(inter)
	with open("/tmp/dumb.pkts","w") as fp:
		fp.write("{}\n".format(first_line))
		for _ in range(600000):
			fp.write("{}\n".format(line))
		fp.write("{}\n".format(last_line))
		fp.flush()
		fp.close()


