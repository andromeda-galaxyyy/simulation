#!/bin/bash


rsync -av  ./traffic/gogen/bin stack@192.168.1.90:/home/stack/code/simulation/traffic/gogen
rsync -av  ./traffic/gogen/bin stack@192.168.1.76:/home/stack/code/simulation/traffic/gogen
