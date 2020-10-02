#!/bin/bash

gpu=$1
n_workers=$2
worker_id=$3

echo "Overall ${n_workers} workers,this is ${worker_id}th worker"
echo "Use gpu:${gpu}"

export export CUDA_VISIBLE_DEVICES=${gpu}

# shellcheck disable=SC2004
# shellcheck disable=SC2034
n_task_per_worker=$(( 66/${n_workers} ))

echo "${n_task_per_worker} tasks per worker"

all_ids=({0..65})

start_id=$(( worker_id*n_task_per_worker ))

echo $start_id

my_tasks=("${all_ids[@]:${start_id}:${n_task_per_worker}}")

echo "${my_tasks[@]}"

for i in "${my_tasks[@]}";do
  python ./routing/nn/minor.main.py --id "${i}"
done
