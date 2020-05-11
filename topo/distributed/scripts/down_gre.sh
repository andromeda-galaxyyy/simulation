#!/bin/bash
if [[ $EUID -ne 0 ]];then
    echo "this script must be run as root"
    exit 1
fi 

if test "$#" -ne 1;then 
    echo "number of parameters must be 1"
fi

gre="$1"

echo "now tearing down gretap $gre"

ip link del $gre

echo "tear down $gre ok"