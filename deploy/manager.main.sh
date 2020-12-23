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
elif [[ $prj -eq 0 ]]
then
      python ./topo/distributed/main.py \
  --config "${root_dir}/static/demo.config.json" \
  --topos_fn "${root_dir}/static/demo.pkl"
else
  echo "Invalid project"
fi
