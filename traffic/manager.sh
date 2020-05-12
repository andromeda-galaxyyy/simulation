#!/usr/bin/env bash

#accpet ip_file controller_ip controller port
if [[ $# -ne 3 ]];then
echo "Usage:"
echo "manager.sh ip_file controller_ip controller_socket_port"
exit -1
fi;

ip_file=$1
# check ip file
if [[ ! -f ${ip_file} ]];
then
    echo "ip file not exits"
    exit -1
fi

controller_ip=$2
# TODO validate ip

controller_port=$3

root_dir=`dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )`
ditg_bin_dir="$root_dir/traffic/ditg/bin"
exec_file="$ditg_bin_dir/DummyManager"

if [[ ! -f ${exec_file} ]];
then
    echo "compile ditg first!"
    exit -1
fi

while :
do
    ${exec_file} ${ip_file} 2 100 ${controller_ip} ${controller_port}
    sleep 1
done