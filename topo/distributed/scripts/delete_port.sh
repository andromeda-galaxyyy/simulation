#!/usr/bin/env bash
if [[ $EUID -ne 0 ]];then
    echo "This script must be run as root"
    exit 1
fi

if test "$#" -ne 1;then
    echo "Number of parameters must be 1"
    echo "Usage: delete_port.sh port"
    exit 1
fi

port=$1
echo "Deleting port $port"

ip link del $port

tc qdisc del dev $port root netem

echo "Done"
