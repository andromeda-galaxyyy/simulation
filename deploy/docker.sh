#!/usr/bin/env bash

#ssh-keygen -f "/home/stack/.ssh/known_hosts" -R "[localhost]:8101"
docker stop onos22
docker rm onos22
service docker restart
docker run -t -d -p 8181:8181 -p 8101:8101 -p 6653:6653 -p 1029:1029 -p 1026:1026 -p 5005:5005 -p 830:830 -p 7896:7896 --name onos22 onosproject/onos:2.2-latest

