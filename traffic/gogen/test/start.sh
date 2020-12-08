#!/bin/bash

for i in {1..8};
do
  nohup ./bin/gogen   --loss --workers 2 -rip 10.211.55.2 >/dev/null 2>&1 &
done