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

type pktlosswriter struct {
	id int
	flowsPerFile int
	dir string
	channel chan *common.FlowDesc
	cache []*common.FlowDesc
}

func NewPktLossWriter(fPerFile int,dir string,channel chan *common.FlowDesc) *pktlosswriter {
	return &pktlosswriter{
		flowsPerFile: fPerFile,
		dir:          dir,
		channel:      channel,
		cache: make([]*common.FlowDesc,0),
	}
}

func (w *pktlosswriter)generateFn() string  {
	return path.Join(w.dir,fmt.Sprintf("%d.%s",w.id,utils.NowInString()))
}

func (w *pktlosswriter)start()  {
	defer w.flush()
	for f:=range w.channel{
		w.cache=append(w.cache,f)
		if w.flowsPerFile<=len(w.cache){
			//write to file
			fn:=w.generateFn()
			w.write(w.cache,w.generateFn())
			log.Printf("Write pkt loss stats to file %s\n",fn)
			w.cache=make([]*common.FlowDesc,0)
		}
	}
}

func (w *pktlosswriter)flush()  {
	log.Println("Packet loss writer,flush cache")
	if len(w.cache)==0{
		log.Println("No need to flush cache")
	}
	fn:=w.generateFn()
	log.Printf("flush pkt loss stats to file %s\n",fn)
	w.write(w.cache,fn)
}


//todo add timeout
func (w *pktlosswriter)write(flows []*common.FlowDesc,filepath string)  {
	f,err:=os.Create(filepath)
	if err!=nil{
		log.Fatalf("Cannot create file %s",filepath)
	}
	defer f.Close()

	errors:=make([]error,0)

	bufferWriter:=bufio.NewWriter(f)
	bufferWriter.WriteString(fmt.Sprintf("%s\n",common.TxLossHeader()))
	for _,f:=range flows{
		_,err=bufferWriter.WriteString(fmt.Sprintf("%s\n",f.ToTxLossStats()))
		if err!=nil{
			errors=append(errors,err)
		}
	}

	err=bufferWriter.Flush()
	if err!=nil{
		log.Fatalf("Cannot complete flush to file %s",filepath)
	}
}



