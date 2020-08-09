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

func GenerateDirNameFromTime() string  {
	return utils.NowInString()
}

type writer struct {
	id                int
	baseDelayStatsDir string
	basePktStatsDir string

	numItemsPerFile   int64
	numFilesPerDir    int64
	dirnameGenerator  DirNameGenerator
	flowChannel       chan *common.FlowDesc

	//cacheA []*flowDesc
	//cacheB []*flowDesc
	cache []*common.FlowDesc
	currentCache []*common.FlowDesc
	current int

	//
	filesInDir        int64
	currDelayStatsDir string
	currPktLossStatsDir string
	enablePktLossStats bool
}




func NewWriter(id int, delayBaseDir string,lossBaseDir string,itemsPerFile int64,filesPerDir int64,dirnameGenerator DirNameGenerator,channel chan *common.FlowDesc) *writer {
	w:=&writer{
		id:                id,
		baseDelayStatsDir: delayBaseDir,
		basePktStatsDir: lossBaseDir,
		numItemsPerFile:   itemsPerFile,
		numFilesPerDir:    filesPerDir,
		dirnameGenerator:  dirnameGenerator,
		flowChannel:       channel,
		cache:             make([]*common.FlowDesc,0),

	}
	w.current=0

	return w
}

func NewDefaultWriter(id int,channel chan *common.FlowDesc)*writer {
	return NewWriter(id,delayBaseDir,pktLossBaseDir,10,1000,GenerateDirNameFromTime,channel)
}

func (w *writer)Flush()  {
	if len(w.cache)==0{
			log.Printf("writer :%d,No need to completeFlush\n",w.id)
			return
	}
	dirname:=path.Join(w.baseDelayStatsDir,w.dirnameGenerator())
	_=utils.CreateDir(dirname)
	fn:=path.Join(dirname,utils.NowInString())
	w.writeDelayStats(w.cache,fn)

	if w.enablePktLossStats{
		dirname:=path.Join(w.basePktStatsDir,w.dirnameGenerator())
		_=utils.CreateDir(dirname)
		fn:=path.Join(dirname,utils.NowInString())
		w.writePktLossStats(w.cache,fn)
	}
}


func (w *writer) Start()  {
	defer w.Flush()
	for f:=range w.flowChannel {
		w.cache=append(w.cache,f)
		if int64(len(w.cache))>=w.numItemsPerFile{
				if w.filesInDir>=w.numFilesPerDir ||w.currDelayStatsDir ==""||w.currPktLossStatsDir==""{
					dir1 :=path.Join(w.baseDelayStatsDir,w.dirnameGenerator())
					err:=utils.CreateDir(dir1)
					if err!=nil{
						log.Fatalf("Error Create delayStatsDir %s\n", dir1)
					}
					w.currDelayStatsDir = dir1

					dir2 :=path.Join(w.baseDelayStatsDir,w.dirnameGenerator())
					err=utils.CreateDir(dir2)
					if err!=nil{
						log.Fatalf("Error Create dir1 %s\n", dir1)
					}
					w.currPktLossStatsDir = dir2
					w.filesInDir=0
				}
				fn:=path.Join(w.currDelayStatsDir,utils.NowInString())
				log.Printf("Write pkt delay stats to file %s\n",fn)
				w.writeDelayStats(w.cache,fn)

				if w.enablePktLossStats{
					fn:=path.Join(w.currPktLossStatsDir,utils.NowInString())
					log.Printf("Write pkt loss stats to file %s\n",fn)
					w.writePktLossStats(w.cache,fn)
				}
				w.cache=make([]*common.FlowDesc,0)
				w.filesInDir+=1
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

	for _, f := range flows {

		_,err=pktLossWriter.WriteString(fmt.Sprintf("%s\n",f.ToLossRateStats()))
		if err!=nil{
			errors=append(errors,err)
		}
	}

	err=pktLossWriter.Flush()

	if err!=nil{
		log.Fatalf("cannot flush pkt loss stats file:%s\n",pktLossStatsFn)
	}
}


