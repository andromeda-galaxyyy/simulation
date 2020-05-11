#!/usr/bin/env bash

if [[ $EUID -ne 0 ]];then
    echo "This script must be run as root"
    exit 1
fi

if test "$#" -ne 4;then
    echo "number of paramters must be 4"
    echo "Usage: local_link.sh switch_a switch_b delay bandwidth"
fi

sa=$1
sb=$2
delay=$3
bandwidth=$4

echo "Set up link between $sa $sb, delay $delay,bandwidth $bandwidth"

port="$sa$sb"
peer_port="$sb$sa"

ip link add $port type veth peer name $peer_port

ifconfig $port up
ifconfig $peer_port up

ovs-vsctl add-port $sa $port
ovs-vsctl add-port $sb $peer_port

tc qdisc add dev $port root netem rate $bandwidth latency $delay
tc qdisc add dev $peer_port root netem rate $bandwidth latency $delay

echo "Done"