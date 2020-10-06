#!/bin/bash


for model_id in {0..65};
  do
#    echo $model_id
    nohup python ./routing/nn/minor.server.py --id $model_id >/tmp/minor.server.${model_id}.log 2>&1 &
  done


