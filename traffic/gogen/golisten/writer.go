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

	numItemsPerFile  int64
	dirnameGenerator DirNameGenerator
	delayChannel     chan *common.FlowDesc
	lossChannel      chan *common.FlowDesc

	delayCache []*common.FlowDesc
	lossCache []*common.FlowDesc

	enablePktLossStats bool
	sigChan            chan common.Signal
}




func NewWriter(id int, delayBaseDir string,lossBaseDir string,itemsPerFile int64,channel chan *common.FlowDesc) *writer {
	w:=&writer{
		id:              id,
		delayStatsDir:   delayBaseDir,
		pktLossStatsDir: lossBaseDir,
		numItemsPerFile: itemsPerFile,
		delayChannel:    channel,
		delayCache:      make([]*common.FlowDesc,0),
	}

	return w
}

func NewDefaultWriter(id int,channel chan *common.FlowDesc)*writer {
	return NewWriter(id,delayBaseDir,pktLossBaseDir,itemsPerFile,channel)
}

func (w *writer) FlushDelayStats()  {
	if len(w.delayCache)==0&&len(w.lossCache)==0{
		log.Printf("writer :%d,No need to completeFlush\n",w.id)
		return
	}
	filename:=fmt.Sprintf("%d.%d.%s.%s",lid,w.id,utils.NowInString(),"delay")
	fn:=path.Join(w.delayStatsDir,filename)
	w.writeDelayStats(w.delayCache,fn)

	if enablePktLossStats{
		filename:=fmt.Sprintf("%d.%d.%s.%s",lid,w.id,utils.NowInString(),"loss")
		fn:=path.Join(w.pktLossStatsDir,filename)
		w.writePktLossStats(w.lossCache,fn)
	}
	w.delayCache =make([]*common.FlowDesc,0)
	w.lossCache=make([]*common.FlowDesc,0)
}

func (w *writer)FlushLossStats()  {
	if len(w.lossCache)==0{
		log.Printf("writer :%d,No need to completeFlush\n",w.id)
		return
	}

	filename:=fmt.Sprintf("%d.%d.%s.%s",lid,w.id,utils.NowInString(),"loss")
	fn:=path.Join(w.pktLossStatsDir,filename)
	w.writePktLossStats(w.lossCache,fn)
	w.lossCache=make([]*common.FlowDesc,0)
}

func (w *writer)Flush()  {
	w.FlushDelayStats()
	w.FlushLossStats()
}


func (w *writer) acceptDelayDesc(f *common.FlowDesc){
	if nil==f{
		return
	}
	w.delayCache =append(w.delayCache,f)
	if int64(len(w.delayCache))>=w.numItemsPerFile{
		fn:=path.Join(w.delayStatsDir,fmt.Sprintf("%d.%d.%s.%s",lid,w.id,utils.NowInString(),"delay"))
		log.Printf("Write pkt delay stats to file %s\n",fn)
		w.writeDelayStats(w.delayCache,fn)
		w.delayCache =make([]*common.FlowDesc,0)
	}
}


func (w *writer) acceptLossDesc(f *common.FlowDesc){
	if nil==f{
		return
	}
	w.lossCache =append(w.lossCache,f)
	if int64(len(w.lossCache))>=w.numItemsPerFile{
		fn:=path.Join(w.pktLossStatsDir,fmt.Sprintf("%d.%d.%s.%s",lid,w.id,utils.NowInString(),"loss"))
		log.Printf("Write pkt loss stats to file %s\n",fn)
		w.writePktLossStats(w.lossCache,fn)
		w.lossCache =make([]*common.FlowDesc,0)
	}
}



func (w *writer) Start()  {
	defer w.Flush()
	if enablePeriodicalFlush{
		stopped:=false
		for{
			if stopped{
				break
			}
			select {
			case sig:=<-w.sigChan:
				if sig.Type==common.StopSignal.Type{
					log.Printf("Writer id :%d stop requested",w.id)
					stopped=true
					break
				}else if sig.Type==common.FlushSignal.Type{
					log.Printf("Writer id: %d periodical flush",w.id)
					w.Flush()
					//w.FlushDelayStats()
					break
				}
			case f:=<-w.delayChannel:
				w.acceptDelayDesc(f)
				break
			case f:=<-w.lossChannel:
				w.acceptLossDesc(f)
				break
			}
		}
	}else{
		stopped:=false
	loop:
		for {
			if stopped{
				break
			}
			select {
			case sig:=<-w.sigChan:
				if sig.Type==common.StopSignal.Type{
					stopped=true
					break loop
				}
			case f:=<-w.delayChannel:
				w.acceptDelayDesc(f)
				break
			case f:=<-w.lossChannel:
				w.acceptLossDesc(f)
				break
			}
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


