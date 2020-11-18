#!/usr/bin/env bash

#ssh-keygen -f "/home/stack/.ssh/known_hosts" -R "[localhost]:8101"
docker stop onoslatest
docker rm onoslatest

docker stop redis_instance
docker rm redis_instance

# service docker restart
sleep 1

docker run -t -d -p 8181:8181 -p 8101:8101 -p 6654:6653 -p 1029:1029 -p 1026:1026 -p 5005:5005 -p 830:830 -p 7896:7896 --name onoslatest onosproject/onos:latest
docker run -d --name redis_instance -p 6379:6379 redis
