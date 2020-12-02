#!/bin/bash

#env GOOS=linux
(cd ./gen &&go  build -o ../bin/gogen && cp ../bin/gogen /tmp/gogen)
(cd ./golisten &&go  build -o ../bin/golisten && cp ../bin/golisten /tmp/golisten)
(cd ./api &&go  build -o ../bin/api && cp ../bin/api /tmp/api)
(cd ./collector &&go  build -o ../bin/collector && cp ../bin/collector /tmp/collector)
(cd ./classifier && go build -o ../bin/classifier && cp ../bin/classifier /tmp/classifier)
