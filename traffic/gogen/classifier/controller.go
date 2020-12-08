package main

import (
	"chandler.com/gogen/common"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
)

type controller struct {
	pktDir string
	wg *sync.WaitGroup
	nWorkers int
	workers []*worker
}

func (c *controller)init()  {
	c.wg=&sync.WaitGroup{}
	c.wg.Add(c.nWorkers)
	c.workers=make([]*worker,0)
	for i:=0;i<c.nWorkers;i++{
		c.workers=append(c.workers,&worker{
			id:              i,
			pkts_dir:        "",
			doneChan:        make(chan common.Signal,1),
			wg: c.wg,
		})
	}
	sigs:=make(chan os.Signal,1)
	signal.Notify(sigs,syscall.SIGINT,syscall.SIGTERM,syscall.SIGKILL)
	go func() {
		sig:=<-sigs
		log.Printf("recevied signal %s,shuting down worker\n",sig)
		for wid,w:=range c.workers{
			log.Printf("Prepare to shutting done worker: %d\n",wid)
			w.doneChan<-common.StopSignal
		}
	}()

}

func (c *controller)start()  {
	for _,w:=range c.workers{
		w.reset()
		go w.start()
	}
	c.wg.Wait()
	log.Println("Controller exit")
}




