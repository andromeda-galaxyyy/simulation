#!/bin/bash

ip netns del h0
ip netns del h1

ip netns add h0
ip netns add h1

ovs-vsctl del-br stest

ip link add h0-eth0 type veth peer name test-h0
ip link add h1-eth0 type veth peer name test-h1


ovs-vsctl add-br stest


ip link set dev h0-eth0 netns h0
ip link set dev h1-eth0 netns h1


ip netns exec h0 ip addr add 10.0.0.1/24 dev h0-eth0
ip netns exec h1 ip addr add 10.0.0.2/24 dev h1-eth0

ip netns exec h0 ip link set dev h0-eth0 up 
ip netns exec h1 ip link set dev h1-eth0 up
ip netns exec h0 ip link set lo up 
ip netns exec h1 ip link set lo up 


ovs-vsctl add-port stest test-h0
ip link set dev test-h0 up
ovs-vsctl add-port stest test-h1
ip link set dev test-h1 up

