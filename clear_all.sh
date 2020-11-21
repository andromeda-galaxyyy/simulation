#!/usr/bin/env bash

for bridge in `ovs-vsctl list-br`; 
do
                ovs-vsctl del-br $bridge
                echo "$bridge" deleted
done

for hid in {0..99}
do
    ip netns del "h${hid}"
done


for name in $(ifconfig -a | sed 's/[ \t].*//;/^\(lo\|\)$/d' | grep "-")
do
    echo $name
    ip link del dev ${name}
done

ip link del dev nat1
ip link del dev nat2

#iptables -P INPUT ACCEPT
#iptables -P FORWARD ACCEPT
#iptables -P OUTPUT ACCEPT
#iptables -t nat -F
#iptables -t mangle -F
#iptables -F
#iptables -X

pkill -f '^gogen$'
pkill -f '^golisten$'
pkill "ovs-tcpdump"
pkill "tcpdump"