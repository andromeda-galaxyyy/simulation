#!/usr/bin/env bash

rsync -av --exclude '*.git' --exclude '*pyc' . stack@192.168.1.90:/home/stack/code/simulation/