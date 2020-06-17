import requests

if __name__ == '__main__':
	requests.post("http://localhost:5000/config",json={"config":{},"id":1,"intf":"eno1"})
	requests.post("http://localhost:5000/topo",json={"topo":[]})


