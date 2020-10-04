#!/bin/bash


function add_tc() {
  local intf=$1
  local delay=$2
  local bw=$3

  tc qdisc add dev "${intf}" root handle 5:0 hfsc default 1
  tc class add dev "${intf}" parent 5:0 classid 5:1 hfsc sc rate "${bw}"Mbit ul rate "${bw}"Mbit
  if [ "$delay" -eq "0" ];then
    return
  fi

  tc qdisc add dev "${intf}" parent 5:1 handle 10: netem delay "${delay}ms"
}



function setup_serv() {
  local serv_phsy_port=$1
  local serv_ovs=$2
  local controller=$3
  local serv_neighbor1=$4
  local serv_neighbor2=$5

  local delay=$6
  local bw=$7

  serv_n1="s${serv_neighbor1}"
  serv_n2="s${serv_neighbor2}"

  echo "Bind port ${serv_phsy_port} to serv_ovs ${serv_ovs}"
  serv_ovs-vsctl del-br "${serv_ovs}"

  serv_ovs-vsctl add-br "${serv_ovs}" -- set bridge "${serv_ovs}" protocols=OpenFlow10,OpenFlow11,OpenFlow12,OpenFlow13
  serv_ovs-vsctl set-controller "${serv_ovs}" tcp:"${controller}"
  serv_ovs-vsctl add-port "${serv_ovs}" "${serv_phsy_port}"

  ip link set "${serv_phsy_port}" up

  ip link del

  ip link add "${serv_ovs}-${serv_n1}" type veth peer name "${serv_n1}-${serv_ovs}"
  ip link add "${serv_ovs}-${serv_n2}" type veth peer name "${serv_n2}-${serv_ovs}"

  serv_ovs-vsctl add-port "${serv_ovs}" "${serv_ovs}-${serv_n1}"
  serv_ovs-vsctl add-port "${serv_ovs}" "${serv_ovs}-${serv_n2}"

  serv_ovs-vsctl add-port "${serv_n1}" "${serv_n1}-${serv_ovs}"
  serv_ovs-vsctl add-port "${serv_n2}" "${serv_n2}-${serv_ovs}"

  ip link set "${serv_ovs}-${serv_n1}" up
  ip link set "${serv_n1}-${serv_ovs}" up
  ip link set "${serv_ovs}-${serv_n2}" up
  ip link set "${serv_n2}-${serv_ovs}" up

  add_tc "${serv_ovs}-${serv_n1}" "$delay" "$bw"
  add_tc "${serv_n1}-${serv_ovs}" "$delay" "$bw"
  add_tc "${serv_ovs}-${serv_n2}" "$delay" "$bw"
  add_tc "${serv_n2}-${serv_ovs}" "$delay" "$bw"

  echo "Server set up done"
}


function setup_client_access() {
  local
}


serv_phsy_port=$1
serv_ovs=$2
controller=$3
serv_neighbor1=$4
serv_neighbor2=$5
delay=$6
bw=$7

setup_serv "${serv_phsy_port}" "${serv_ovs}"  "${controller}" "${serv_neighbor1}" "${serv_neighbor2}" "${delay}" "$bw"