package main

import (
	"bufio"
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
	id               int
	baseDir          string
	numItemsPerFile  int64
	numFilesPerDir   int64
	dirnameGenerator DirNameGenerator
	flowChannel      chan *flowDesc

	//轮换,防止饱和
	cacheA []*flowDesc
	cacheB []*flowDesc
	currentCache []*flowDesc
	current int

	//
	filesInDir int64
	currentDir string
}




func NewWriter(id int,base string,itemsPerFile int64,filesPerDir int64,dirnameGenerator DirNameGenerator,channel chan *flowDesc) *writer {
	w:=&writer{
		id:               id,
		baseDir:          base,
		numItemsPerFile:  itemsPerFile,
		numFilesPerDir:   filesPerDir,
		dirnameGenerator: dirnameGenerator,
		flowChannel:      channel,
		cacheA:           make([]*flowDesc,0),
		cacheB:           make([]*flowDesc,0),
	}
	w.current=0

	return w
}

func NewDefaultWriter(id int,base string,channel chan *flowDesc)*writer {
	return NewWriter(id,base,10,10,GenerateDirNameFromTime,channel)
}

func (w *writer)Flush()  {
	if len(w.cacheA)==0 && len(w.cacheB)==0{
		log.Printf("writer :%d,No need to flush\n",w.id)
		return
	}
	//

	dirname:=path.Join(w.baseDir,w.dirnameGenerator())
	_=utils.CreateDir(dirname)
	if len(w.cacheB)>0{
		fn1:=path.Join(dirname,utils.NowInString())
		log.Printf("writer %d flush cacheB to file :%s\n",w.id,fn1)
		w.write(w.cacheB,fn1,1)
	}
	if len(w.cacheA)>0{
		fn2:=path.Join(dirname,utils.NowInString())
		log.Printf("writer %d flush cacheA to file :%s\n",w.id,fn2)
		w.write(w.cacheA,fn2,0)
	}
}


func (w *writer)Accept()  {
	defer w.Flush()
	for f:=range w.flowChannel {
		if w.current==0{
			//A cache
			w.cacheA=append(w.cacheA,f)
			w.currentCache=w.cacheA
		}else{
			//cache B
			w.cacheB=append(w.cacheB,f)
			w.currentCache=w.cacheB
		}
		//write flows to file
		if int64(len(w.currentCache))>=w.numItemsPerFile {
			//change cache and start to write
			//todo possible race condition,but very unlikely
			//

			if w.filesInDir>=w.numFilesPerDir ||w.currentDir==""{
				dir:=path.Join(w.baseDir,w.dirnameGenerator())
				err:=utils.CreateDir(dir)
				if err!=nil{
					log.Fatalf("Error Create dir %s\n",dir)
				}
				w.currentDir=dir
				w.filesInDir=0
			}
			fn:=path.Join(w.currentDir,utils.NowInString())
			log.Printf("Write flows to file %s\n",fn)
			if w.current==0{
				go w.write(w.cacheA,fn,w.current)
			}else{
				go w.write(w.cacheB,fn,w.current)
			}

			w.filesInDir+=1
			w.current=1-w.current
		}
	}
}

//perform write=
func (w *writer)write(flows []*flowDesc,fn string,current int) {
	f, err := os.Create(fn)
	errors := make([]error, 0)
	if err != nil {
		log.Fatalf("cannot create file:%s\n", fn)
	}
	defer f.Close()
	bufferWriter := bufio.NewWriter(f)
	for _, f := range flows {
		_, err = bufferWriter.WriteString(fmt.Sprintf("%s\n", f))
		if err != nil {
			errors = append(errors, err)
		}
	}
	err = bufferWriter.Flush()
	if err != nil {
		log.Fatalf("cannot flush file:%s\n", fn)
	}
	if current == 0 {
		w.cacheA = make([]*flowDesc, 0)
	}else{
		w.cacheB=make([]*flowDesc,0)
	}
}
