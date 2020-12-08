#!/bin/bash

iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -t nat -F
iptables -t mangle -F
iptables -F
iptables -X




ip netns del h1
ip netns del h0

ip link del h0-eth0
ip link del h0-nat
ip link del h1-eth0