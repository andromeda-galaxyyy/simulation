from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse, abort
from topo.distributed.topomanager import TopoManager
import atexit

app = Flask(__name__)
api = Api(app)
import loguru

manager: TopoManager = None
import json

logger = loguru.logger


class Config(Resource):
	def get(self):
		global manager
		if manager is None:
			return '', 404
		return json.dumps(manager.config)

	def post(self):
		global manager
		config = request.get_json(force=True)
		logger.debug(config)
		manager = TopoManager(config)
		return '', 200


class Topo(Resource):
	def post(self):
		global manager
		topo = request.get_json(force=True)
		logger.debug(topo)
		if manager is not None:
			manager.diff_topo(topo["topo"])
			return '', 200
		else:
			return '', 404

	def delete(self):
		global manager
		if manager is not None:
			manager.tear_down()
			return '', 200
		else:
			return '', 404


class Traffic(Resource):
	def post(self):
		traffic = request.get_data(force=True)
		return '', 200


api.add_resource(Config, "/config")
api.add_resource(Topo, "/topo")
api.add_resource(Traffic, "/traffic")


@atexit.register
def exit_handler():
	global manager
	if manager is not None:
		manager.tear_down()


if __name__ == '__main__':
	# atexit.register(exit_handler)
	app.run(debug=True)
