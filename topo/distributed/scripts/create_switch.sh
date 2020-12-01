#!/bin/bash
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 
   exit 1
fi

if test "$#" -ne 4; then
    echo "number of parameters must be 4"
    echo "Usage: create_switch.sh OVS HOST HOST_IP CONTROLLER"
    exit 1
fi

OVS=$1
HOST=$2
HOST_IP=$3
#CONTROLLER=$4

HOST_PORT="${HOST}-eth0"
OVS_PORT="${OVS}-eth1"

echo "ovs $OVS host $HOST with ip $HOST_IP controller set to $CONTROLLER"

#set up host 
ip netns add $HOST
ip link add $HOST_PORT type veth peer name $OVS_PORT
ip link set $HOST_PORT netns $HOST

#set up host ip 
ip netns exec $HOST ifconfig $HOST_PORT $HOST_IP/8
ip netns exec $HOST ifconfig lo up 


#set mtu
#ip netns exec $HOST ifconfig $HOST_PORT mtu 1454

#set up ovs
ovs-vsctl add-br $OVS
ovs-vsctl add-port $OVS ${OVS_PORT}
#set up ovs port 

ifconfig $OVS_PORT up

#set controller
#ovs-vsctl set-controller $OVS tcp:$CONTROLLER

echo "set up ok"