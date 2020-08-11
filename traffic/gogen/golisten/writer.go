package main

import (
	"bufio"
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"fmt"
	"log"
	"os"
	"path"
)

type DirNameGenerator func() string

var (
	itemsPerFile int64=20
)

func GenerateDirNameFromTime() string  {
	return utils.NowInString()
}

type writer struct {
	id              int
	delayStatsDir   string
	pktLossStatsDir string

	numItemsPerFile   int64
	dirnameGenerator  DirNameGenerator
	flowChannel       chan *common.FlowDesc

	cache []*common.FlowDesc

	enablePktLossStats bool
}




func NewWriter(id int, delayBaseDir string,lossBaseDir string,itemsPerFile int64,channel chan *common.FlowDesc) *writer {
	w:=&writer{
		id:               id,
		delayStatsDir:    delayBaseDir,
		pktLossStatsDir:  lossBaseDir,
		numItemsPerFile:  itemsPerFile,
		flowChannel:      channel,
		cache:            make([]*common.FlowDesc,0),
	}

	return w
}

func NewDefaultWriter(id int,channel chan *common.FlowDesc)*writer {
	return NewWriter(id,delayBaseDir,pktLossBaseDir,itemsPerFile,channel)
}

func (w *writer)Flush()  {
	if len(w.cache)==0{
			log.Printf("writer :%d,No need to completeFlush\n",w.id)
			return
	}
	filename:=fmt.Sprintf("%d.%d.%s",lid,w.id,utils.NowInString())
	fn:=path.Join(w.delayStatsDir,filename)
	w.writeDelayStats(w.cache,fn)

	if enablePktLossStats{
		filename:=fmt.Sprintf("%d.%d.%s",lid,w.id,utils.NowInString())
		fn:=path.Join(w.pktLossStatsDir,filename)
		w.writePktLossStats(w.cache,fn)
	}
}


func (w *writer) Start()  {
	defer w.Flush()
	for f:=range w.flowChannel {
		w.cache=append(w.cache,f)
		if int64(len(w.cache))>=w.numItemsPerFile{
				fn:=path.Join(w.delayStatsDir,fmt.Sprintf("%d.%d.%s",lid,w.id,utils.NowInString()))
				log.Printf("Write pkt delay stats to file %s\n",fn)
				w.writeDelayStats(w.cache,fn)

				if enablePktLossStats{
					fn:=path.Join(w.pktLossStatsDir,fmt.Sprintf("%d.%d.%s",lid,w.id,utils.NowInString()))
					log.Printf("Write pkt loss stats to file %s\n",fn)
					w.writePktLossStats(w.cache,fn)
				}
				w.cache=make([]*common.FlowDesc,0)
		}
	}
}

//perform writeDelayStats
func (w *writer) writeDelayStats(flows [] *common.FlowDesc, delayStatsFn string) {
	errors := make([]error, 0)

	delayStatsFp, err := os.Create(delayStatsFn)
	if err != nil {
		log.Fatalf("cannot create delay stats file:%s\n", delayStatsFn)
	}
	defer delayStatsFp.Close()


	delayWriter := bufio.NewWriter(delayStatsFp)
	delayWriter.WriteString(fmt.Sprintf("%s\n",common.RxDelayStatsHeader()))
	for _, f := range flows {
		_, err = delayWriter.WriteString(fmt.Sprintf("%s\n", f.ToDelayStats()))
		if err != nil {
			errors = append(errors, err)
		}
	}
	err = delayWriter.Flush()
	if err != nil {
		log.Fatalf("cannot flush pkt delay stats file:%s\n", delayStatsFn)
	}

}

func (w *writer) writePktLossStats(flows [] *common.FlowDesc,pktLossStatsFn string) {
	errors := make([]error, 0)

	pktLossStatsFp,err:=os.Create(pktLossStatsFn)
	if err!=nil{
		log.Fatalf("cannot create pkt stats file:%s\n",pktLossStatsFp)
	}
	defer pktLossStatsFp.Close()
	pktLossWriter:=bufio.NewWriter(pktLossStatsFp)

	pktLossWriter.WriteString(fmt.Sprintf("%s\n",common.RxLossHeader()))

	for _, f := range flows {
		_,err=pktLossWriter.WriteString(fmt.Sprintf("%s\n",f.ToRxLossStats()))
		if err!=nil{
			errors=append(errors,err)
		}
	}

	err=pktLossWriter.Flush()

	if err!=nil{
		log.Fatalf("cannot flush pkt loss stats file:%s\n",pktLossStatsFn)
	}
}


