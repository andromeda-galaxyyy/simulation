#!/usr/bin/env bash
root_dir=`dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )`
ditg_bin_dir="$root_dir/traffic/ditg/bin"
exec_file="$ditg_bin_dir/ITGRecv"
if [[ ! -f ${exec_file} ]];
then
    echo "compile ditg first"
    exit -1
fi

if [[ $@ -eq 0 ]];
then
Sp=1030
else
Sp=$1
fi

echo ${Sp}

while :
do
    ${exec_file} -Sp ${Sp}
    sleep 1
done