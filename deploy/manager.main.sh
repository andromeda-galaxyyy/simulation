#!/bin/bash

root_dir=`dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )`

source "${root_dir}/deploy/python.rc"
clear;

echo $root_dir
echo ">Enter project":
echo ">0. Demo"
echo ">1. Satellite"
echo ">2. Telemetry"
echo ">3. Military"
echo ">4. Rate"
echo "########################"
echo "########################"
echo ">5. Telemetry delay 10ms"
echo ">6. Telemetry delay 20ms"
echo ">7. Telemetry loss 5"
echo ">8. Telemetry loss 10"
echo ">9. Rate on military topo"
echo "#######################"
echo ">10. Military anomaly topo"
read prj
echo "Project ${prj}"


if [[ $prj -eq 1 ]]
then
  python ./topo/distributed/main.py \
  --config "${root_dir}/static/satellite.config.json" \
  --topos_fn "${root_dir}/static/satellite_overall.pkl"
elif [[ $prj -eq 2 ]]
then
   python ./topo/distributed/main.py \
  --config "${root_dir}/topo/distributed/telemetry.config.json" \
  --topos_fn "${root_dir}/static/satellite_overall.pkl"
elif [[ $prj -eq 3 ]]
then
       python ./topo/distributed/main.py \
  --config "${root_dir}/static/military.config.json" \
  --topos_fn "${root_dir}/static/military.pkl"
elif [[ $prj -eq 4 ]]
then
      python ./topo/distributed/main.py \
  --config "${root_dir}/topo/distributed/rate.config.json" \
  --topos_fn "${root_dir}/static/satellite_overall.pkl"
elif [[ $prj -eq 5 ]]
then
       python ./topo/distributed/main.py \
  --config "${root_dir}/static/military.config.json" \
  --topos_fn "${root_dir}/static/military.delay10.pkl"


elif [[ $prj -eq 6 ]]
then
       python ./topo/distributed/main.py \
  --config "${root_dir}/static/military.config.json" \
  --topos_fn "${root_dir}/static/military.delay20.pkl"

elif [[ $prj -eq 7 ]]
then
       python ./topo/distributed/main.py \
  --config "${root_dir}/static/military.config.json" \
  --topos_fn "${root_dir}/static/military.loss5.pkl"

elif [[ $prj -eq 8 ]]
then
       python ./topo/distributed/main.py \
  --config "${root_dir}/static/military.config.json" \
  --topos_fn "${root_dir}/static/military.loss10.pkl"


elif [[ $prj -eq 9 ]]
then
       python ./topo/distributed/main.py \
  --config "${root_dir}/static/military.rate.json" \
  --topos_fn "${root_dir}/static/military.pkl"


elif [[ $prj -eq 10 ]]
then
       python ./topo/distributed/main.py \
  --config "${root_dir}/static/military.config.json" \
  --topos_fn "${root_dir}/static/military.anomaly.pkl"



elif [[ $prj -eq 0 ]]
then
      python ./topo/distributed/main.py \
  --config "${root_dir}/static/demo.config.json" \
  --topos_fn "${root_dir}/static/demo.pkl"
else
  echo "Invalid project"
fi
