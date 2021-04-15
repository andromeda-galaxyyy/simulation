from utils.process_utils import start_new_thread_and_run
from flask import Flask, request, jsonify
from flask_restful import Resource, Api, reqparse, abort
from topo.distributed.topobuilder import TopoBuilder
import json
import atexit
import threading
from utils.log_utils import debug, info, err
from utils.process_utils import start_new_thread_and_run
from path_utils import get_prj_root
from utils.process_utils import start_new_thread_and_run
import os

tmp_dir = os.path.join(get_prj_root(), "topo/distributed/tmp")
iptables_bk = os.path.join(tmp_dir, "iptables.bk")

os.system("iptables-save > {}".format(iptables_bk))
os.system("sysctl -w net.ipv4.ip_forward=1")

app = Flask(__name__)
api = Api(app)

builder: TopoBuilder = None


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
		if builder is not None:
			start_new_thread_and_run(builder.stop, args=[])
		builder = None


class Topo(Resource):
	def post(self):
		global builder
		topo = request.get_json(force=True)
		if builder is not None:
			# start_new_thread_run(builder.diff_topo, [topo["topo"]])
			builder.diff_topo(topo["topo"])
			return '', 200
		else:
			return '', 404

	def delete(self):
		global builder
		debug("tear down topo")
		if builder is not None:
			start_new_thread_and_run(builder.stop, args=[])
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


class Traffic2(Resource):
	def post(self):
		debug("diff traffic mode")
		data = request.get_json(force=True)
		mode = data["mode"]
		builder.diff_traffic_mode(mode)
		return '', 200

	def delete(self):
		debug("stop traffic")
		if builder is not None:
			start_new_thread_and_run(builder.stop_traffic_actor, args=())
		return '', 200


class Supplementry(Resource):
	def post(self):
		debug("Setup supplementary topo")
		data = request.get_json(force=True)
		is_server = data["server"]
		builder.setup_supplementary_topo(is_server=is_server)
		return '', 200


class Supplementary2(Resource):
	def post(self):
		debug("Setup supplementary topo2")
		data = request.get_json(force=True)
		builder.setup_supplementary_topo2(int(data["band"]))


class Telemetry(Resource):
	def post(self):
		debug("Start telemetry")
		data = request.get_json(force=True)
		start_new_thread_and_run(builder.start_telemetry, args=())
		return '', 200

	def delete(self):
		debug("Stop telemetry")
		if builder is not None:
			start_new_thread_and_run(builder.stop_telemetry, args=())
		return '', 200


class Classifier(Resource):
	def post(self):
		debug("start classifier demo")
		if builder is None:
			return '', 404
		builder.start_classifier_demo()
		return '', 200

	def delete(self):
		debug("stop classifier")
		if builder is None:
			return '', 404
		builder.stop_classifier_demo()
		return '', 200


class AnomalySupplementary(Resource):
	def post(self):
		debug("setup anomaly supplementary topo")
		if builder is None:
			return '', 404
		builder.setup_anomaly_supplementary_topo()
		return '', 200

class AnomalyTraffic(Resource):
	def post(self):
		debug("router start anomaly traffic")
		if builder is None:
			return '',404
		builder.start_anomaly_traffic()
		return '',200

	def delete(self):
		if builder is None:
			return '',404
		builder.stop_anomaly_traffic()
		return '',200


api.add_resource(Config, "/config")
api.add_resource(Topo, "/topo")
api.add_resource(Traffic, "/traffic")
api.add_resource(Supplementry, "/supplementary")
api.add_resource(Supplementary2, "/supplementary2")
api.add_resource(Traffic2, "/traffic2")
api.add_resource(Telemetry, "/telemetry")
api.add_resource(Classifier, "/classifier")
api.add_resource(AnomalySupplementary, "/anomaly")
api.add_resource(AnomalyTraffic,"/anomaly_traffic")



@atexit.register
def exit_handler():
	global builder
	if builder is not None:
		debug("Exit router... start to tear done topo")
		builder.stop()
		debug("Router exited...topo tear down")


if __name__ == '__main__':
	atexit.register(exit_handler)
	app.run(host="0.0.0.0", port=5000)
