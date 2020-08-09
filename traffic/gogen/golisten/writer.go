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

	//cacheA []*flowDesc
	//cacheB []*flowDesc
	cache []*flowDesc
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
		cache: make([]*flowDesc,0),

	}
	w.current=0

	return w
}

func NewDefaultWriter(id int,base string,channel chan *flowDesc)*writer {
	return NewWriter(id,base,10,1000,GenerateDirNameFromTime,channel)
}

func (w *writer)Flush()  {
	if len(w.cache)==0{
			log.Printf("writer :%d,No need to completeFlush\n",w.id)
			return
	}
	dirname:=path.Join(w.baseDir,w.dirnameGenerator())
	_=utils.CreateDir(dirname)
	fn:=path.Join(dirname,utils.NowInString())
	w.write(w.cache,fn)
}


func (w *writer) Start()  {
	defer w.Flush()
	for f:=range w.flowChannel {
		w.cache=append(w.cache,f)
		if int64(len(w.cache))>=w.numItemsPerFile{
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
				w.write(w.cache,fn)
				w.cache=make([]*flowDesc,0)
				w.filesInDir+=1
		}
	}
}

//perform write=
func (w *writer)write(flows []*flowDesc,fn string) {
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
		log.Fatalf("cannot completeFlush file:%s\n", fn)
	}
}
