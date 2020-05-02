#!/usr/bin/env bash
result=1
while [ $result -ne 0 ];do
    ITGSend -Q
    result=$?
done