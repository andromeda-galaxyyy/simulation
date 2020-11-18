#!/usr/bin/env bash

#ssh-keygen -f "/home/stack/.ssh/known_hosts" -R "[localhost]:8101"
docker stop onosrate
docker rm onosrate

# docker stop redis_instance
# docker rm redis_instance

#service docker restart
sleep 1

docker run -t -d -p 8183:8181 -p 8103:8101 -p 6655:6653 -p 1031:1029 -p 1028:1026 -p 5007:5005 -p 832:830 -p 7898:7896 --name onosrate onosproject/onos:2.2-latest
# docker run -d --name redis_instance -p 6381:6379 redis