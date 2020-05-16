#!/usr/bin/env bash
exe=$1
if [[ ! -f ${exe} ]];
then
echo "Cannot find exec file ${exe}"
fi

while :
    do ${exe} ${@:2}
    sleep 1
done

