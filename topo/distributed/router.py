from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse, abort
from topo.distributed.topobuilder import TopoBuilder
import json
import atexit
import threading
from utils.log_utils import debug, info, err

app = Flask(__name__)
api = Api(app)

builder: TopoBuilder = None


def start_new_thread_run(f, args):
	threading.Thread(target=f, args=args).start()


class Config(Resource):
	def get(self):
		global builder
		if builder is None:
			return '', 404
		return json.dumps(builder.config)

	def post(self):
		global builder
		obj = request.get_json(force=True)
		config = obj["config"]
		id_ = obj["id"]
		intf = obj["intf"]
		builder = TopoBuilder(config, id_, intf)
		return '', 200

	def delete(self):
		global builder
		builder.stop()
		builder = None


class Topo(Resource):
	def post(self):
		global builder
		topo = request.get_json(force=True)
		if builder is not None:
			start_new_thread_run(builder.diff_topo,[topo["topo"]])
			# builder.diff_topo(topo["topo"])
			return '', 200
		else:
			return '', 404

	def delete(self):
		global builder
		debug("tear down topo")
		if builder is not None:
			builder.stop()
			return '', 200
		else:
			return '', 404


class Traffic(Resource):
	def post(self):
		debug("start topo")
		traffic = request.get_data()
		threading.Thread(target=builder.start_gen_traffic_use_scheduler).start()
		# builder.start_gen_traffic_use_scheduler()
		return '', 200

	def delete(self):
		debug("stop topo")
		threading.Thread(target=builder.stop_traffic_use_scheduler).start()
		# builder.stop_traffic_use_scheduler()
		return '', 200


api.add_resource(Config, "/config")
api.add_resource(Topo, "/topo")
api.add_resource(Traffic, "/traffic")


@atexit.register
def exit_handler():
	global builder
	if builder is not None:
		builder.stop()


if __name__ == '__main__':
	atexit.register(exit_handler)
	app.run(host="0.0.0.0", port=5000)
