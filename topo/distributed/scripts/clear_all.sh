#!/usr/bin/env bash

for bridge in `ovs-vsctl list-br`; 
do
                ovs-vsctl del-br $bridge
done

for hid in {0..66}
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
iptables -F