#!/usr/bin/env bash

root_dir=`dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )`


haproxy_cfg=${root_dir}/deploy/haproxy.cfg
echo ${haproxy}

pgrep haproxy|xargs kill -9
pgrep python|xargs kill -9

for port in {2000..2019}
do
    nohup python ./classify/server.py --port ${port} >/tmp/${port}.log 2>&1 &
done


nohup haproxy -f ${haproxy_cfg} >/dev/null 2>&1 &



