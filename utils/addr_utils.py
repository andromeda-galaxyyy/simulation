import ipaddress
from ipaddress import IPv4Address


def get_ipv4net_prefix(ip: str) -> int:
	return int(ip.split("/")[1])


def get_ipv4net_address(ip: str) -> str:
	net: IPv4Address = ipaddress.ip_network(ip, strict=False)
	return "{}/{}".format(net.network_address, get_ipv4net_prefix(ip))
# return str(net.network_address)


# net:IPv4Address= ipaddress.ip_network(ip, strict=False)
# return int(str(net.network_address).split("/")[1])
