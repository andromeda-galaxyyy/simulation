#!/usr/bin/env bash
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.34:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.90:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.110:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.128:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.180:/home/stack/code/simulation/

# for computing
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.196:/home/stack/code/simulation/
# gpu
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.36:/home/stack/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . stack@192.168.1.132:/home/stack/code/simulation/

#rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . yx@192.168.1.196:/home/yx/code/simulation/
#rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . yx@192.168.1.76:/home/yx/code/simulation/
#rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . yx@192.168.1.90:/home/yx/code/simulation/
rsync -av --exclude '*.git' --exclude '*pyc' --exclude '__pycache__' --exclude 'video.bk' . gjl@192.168.1.90:/home/gjl/code/simulation/

