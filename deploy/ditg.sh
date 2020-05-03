#!/usr/bin/env bash

root_dir=`dirname $( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )`
echo "root dir is $root_dir"

sudo apt update
sudo apt install make g++

ditg_srcdir="traffic/ditg/src"
(cd "${root_dir}/${ditg_srcdir}" && make clean &&  make)

