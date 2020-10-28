#!/usr/bin/env bash

rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.36:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.132:/home/stack/code/simulation/
