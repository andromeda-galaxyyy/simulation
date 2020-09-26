#!/usr/bin/env bash

rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.196:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.76:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.90:/home/stack/code/simulation/
