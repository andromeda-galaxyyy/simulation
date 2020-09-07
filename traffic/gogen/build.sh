#!/bin/bash

(cd ./gen && go build -o ../bin/gogen && cp ../bin/gogen /tmp/gogen)
(cd ./golisten && go build -o ../bin/golisten && cp ../bin/golisten /tmp/golisten)