#!/usr/bin/env bash

result=1
if [ $# -ne 1 ];then
echo "IP file!"
exit -1
fi;

while :
do
    ITGManager $1 1 190 192.168.64.5 10000
    result=$?
done