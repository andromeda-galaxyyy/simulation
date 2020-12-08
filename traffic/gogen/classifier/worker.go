package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"log"
	"sync"
)

type worker struct{
	id int
	pkts_dir string
	doneChan chan common.Signal
	hasReportedSet *utils.IntSet
	wg *sync.WaitGroup

	flowIdToPktSize map[int][]float64
	flowIdToPktIdt map[int][]float64
}

func (w *worker)start()  {
	stopped:=false
	//shuffle
	for{
		if stopped{
			break
		}
		var lines =make([]string,1)
		//read line
		for _,line:=range lines{
			if stopped{
				break
			}
			select {
			case <-w.doneChan:
				log.Printf("Worker %d exit",w.id)
				stopped=true
				break
			default:
				log.Println(line)
				//read line and store stats
			}
		}

	}
	w.wg.Done()
}

func (w *worker)reset(){
	w.hasReportedSet=utils.NewIntSet()
	w.flowIdToPktIdt=make(map[int][]float64)
	w.flowIdToPktSize=make(map[int][]float64)
}

