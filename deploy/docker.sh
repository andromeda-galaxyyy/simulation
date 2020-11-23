#!/usr/bin/env bash

#ssh-keygen -f "/home/stack/.ssh/known_hosts" -R "[localhost]:8101"
docker stop onos22
docker rm onos22

docker stop redis_instance
docker rm redis_instance

# service docker restart
docker run -t -d -p 8181:8181 -p 8101:8101 -p 6654:6653 -p 1029:1029 -p 1026:1026 -p 5005:5005 -p 830:830 -p 7896:7896 -p 1041:1031 --name onos22 onosproject/onos:2.2-latest
docker run -d --name redis_instance -p 6379:6379 redis

echo "Sleep for 20 seconds"
sleep 20


ssh-keygen -f "/root/.ssh/known_hosts" -R "[localhost]:8101"

sshpass -p "karaf" ssh localhost "app activate org.onosproject.fwd"
sshpass -p "karaf" ssh localhost "app activate org.onosproject.openflow"
sshpass -p "karaf" ssh localhost "app activate org.onosproject.proxyarp"

docker cp /home/yx/commmands.json onos22:/home/

echo "Onos docker setup done"
