#!/bin/bash

(cd ./gen && go build -o /tmp/gen)
(cd ./golisten && go build -o /tmp/listen)