#!/bin/bash


(cd ./gen && go build && cp ./gen /tmp/)
(cd ./golisten && go build && cp ./golisten /tmp/)