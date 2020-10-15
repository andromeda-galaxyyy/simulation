package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"fmt"
	"github.com/fsnotify/fsnotify"
	"log"
	"strings"
)


var (
	strict bool=false
)

func IsDelayFile(fn string) bool{
	return strings.Contains(fn,"delay")
}




type Watcher struct {
	id int
	dirs []string
	done chan common.Signal
	worker *fsnotify.Watcher
	//delay channel
	delayChan chan string
	//loss channel
	lossChan chan string
	// 通用channel
	fileChan chan string

	isDelay func(fn string) bool
}



func (watcher *Watcher)String() string{
	return fmt.Sprintf("Watcher:%d",watcher.id)
}

func (w *Watcher) Init()  {
	if 0==len(w.dirs){
		log.Fatalf("Watcher:%d no directories!\n",w.id)
	}
	worker,err:=fsnotify.NewWatcher()
	if nil!=err{
		log.Fatalf("Watcher:%d Cannot create file watcher\n",w.id)
	}
	w.worker=worker

	for _,dir:=range w.dirs{
		if !utils.IsDir(dir){
			log.Fatalf("Watcher:%d Directory:[%s] not exsits!",w.id,dir)
		}
		err=w.worker.Add(dir)
		if err!=nil{
			log.Fatalf("Watcher")
		}
		log.Printf("%s watch %s",w,dir)
	}

	log.Println("Watcher initiated")
}

func (w *Watcher) DemoStart() (e error)  {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		log.Fatal(err)
	}
	defer watcher.Close()

	done := make(chan bool)
	go func() {
		for {
			select {
			case event, ok := <-watcher.Events:
				if !ok {
					return
				}
				log.Println("event:", event)
				if event.Op&fsnotify.Write == fsnotify.Write {
					log.Println("modified file:", event.Name)
				}
			case err, ok := <-watcher.Errors:
				if !ok {
					return
				}
				log.Println("error:", err)
			}
		}
	}()

	err = watcher.Add("/tmp/foo")
	if err != nil {
		log.Fatal(err)
	}
	<-done
	return nil
}

func (w *Watcher)Start()  {
	defer w.worker.Close()
	for{
		select {
		case event,ok:=<-w.worker.Events:
			if !ok{
				log.Fatalf("%s watcher channel pannic\n",w)
			}
			////log.Println("event:",event)
			//if event.Op&fsnotify.Create==fsnotify.Create{
			//	//log.Printf("[%s] create file :%s\n",w,event.Name)
			//}
			// 创建了新的文件
			if event.Op&fsnotify.Write==fsnotify.Write{
				//log.Printf("[%s] modified file: %s\n",w,event.Name)
				if utils.IsDir(event.Name){
					err:=w.worker.Add(event.Name)
					if nil!=err{
						log.Printf("%s cannot watch %s\n",w,event.Name)
					}
				}else if utils.IsFile(event.Name){
					if w.isDelay(event.Name){
						w.delayChan<-event.Name
					}else{
						w.lossChan<-event.Name
					}
				}
			}
		case <-w.done:
			log.Printf("Shutdown watcher:%s",w)
			return
		}
	}
}

