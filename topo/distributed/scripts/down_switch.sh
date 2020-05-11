#!/bin/bash
if [[ $EUID -ne 0 ]]; then
    echo "This script must run as root"
    exit 1
fi

if test "$#" -ne 2;then
    echo "number of parameters must be 2"
    echo "useage down_switch.sh ovs host"
    exit 1
fi 

OVS=$1
HOST=$2
OVS_PORT="${OVS}-eth1"
HOST_PORT="${HOST}-eth0"


echo "now tearing down $OVS $HOST"
#del host
ip netns del $HOST

ip link del $HOST_PORT


#del ovs
ovs-vsctl del-port $OVS $OVS_PORT
ovs-vsctl del-br $OVS
ip link del $OVS_PORT

echo "tear down ok"