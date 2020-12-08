package main

import (
	"flag"
)

func main()  {
	pktsDir:=flag.String("pkts_dir","/home/stack/code/graduate/sim/system/traffic/gogen/pkts/default","pkts dir")
	nWorker:=flag.Int("workers",8,"Number of workers")
	c:=&controller{
		nWorkers: *nWorker,
		pktDir: *pktsDir,
	}
	c.init()
	c.start()
}
