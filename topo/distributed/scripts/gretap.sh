#!/bin/bash

if [[ $EUID -ne 0 ]];then
    echo "This script must be run as root"
    exit 1
fi

if test "$#" -ne 6;then
    echo "number of parameters must be 4"
    echo "usage gretap.sh gretap_interface local_ip remote_ip key delay bandwidth"
    exit 1
fi

gre=$1
local_ip=$2
remote_ip=$3
key=$4

#delay=$5
#bandwidth=$6

echo "Creating tunnel... $gre from $local_ip to $remote_ip key $key delay $delay bandwidth $bandwidth"

ip link del $gre 
ip link add $gre type gretap local $local_ip remote $remote_ip ttl 64 key $key 
ip link set dev $gre up
#tc qdisc add dev $gre root netem latency $delay rate $bandwidth
ethtool -K $gre gro off
ethtool -K $gre tso off
ethtool -K $gre gso off

echo "Done"
