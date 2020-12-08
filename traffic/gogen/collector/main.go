package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"flag"
	"log"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"syscall"
)

var (
	defaultDirs string
	rport int=6379
	rip string="localhost"
)


func main()  {
	base_dir :=flag.String("base","/tmp/listener_log","Base directory to watch")
	redisPort:=flag.Int("rport",6379,"Redis instance port")
	redisIp:=flag.String("rip","10.211.55.2","Redis instance ip")
	dirs:=flag.String("dirs","/tmp/rxloss,/tmp/rxdelay","Directory to watch")

	flag.Parse()
	rport=*redisPort
	rip=*redisIp


	dd:=make([]string,0)
	filepath.Walk(*base_dir, func(path string, info os.FileInfo, err error) error {
		if info!=nil&&info.IsDir(){
			dd=append(dd,path)
		}
		if err!=nil{
			log.Fatalf("Error when scanning base directory %s\n",*base_dir)
		}
		return nil
	})

	for _,d:=range strings.Split(*dirs,","){
		if utils.IsDir(d){
			dd=append(dd,d)
		}
	}



	delayChan:=make(chan string,10240)
	lossChan:=make(chan string,10240)
	fileChan:=make(chan string,10240)
	doneChanToWatcher :=make(chan common.Signal,1)
	doneChanToWriter:=make(chan common.Signal,1)

	sigs:=make(chan os.Signal,1)
	signal.Notify(sigs,syscall.SIGINT,syscall.SIGTERM,syscall.SIGKILL)


	redisWriter := NewDefaultRedisWriter(*redisIp,*redisPort)
	redisWriter.delayChan=delayChan
	redisWriter.lossChan=lossChan
	redisWriter.fileChan=fileChan
	redisWriter.doneChan=doneChanToWriter

	err:=redisWriter.Init()
	if err!=nil{
		log.Fatalf("Error when connect to redis instance")
	}
	go redisWriter.Start()

	watcher:=&Watcher{
		id:        0,
		dirs:      dd,
		done:      doneChanToWatcher,
		worker:    nil,
		delayChan: delayChan,
		lossChan:  lossChan,
		fileChan:  fileChan,
		isDelay:   IsDelayFile,
	}
	watcher.Init()
	go watcher.Start()

	quit:=make(chan common.Signal,1)
	go func() {
		<-sigs
		log.Println("Stop requested")
		log.Println("Send stop signal to watcher")
		doneChanToWatcher<-common.StopSignal
		log.Println("Send stop signal to writer")
		doneChanToWatcher<-common.StopSignal
		log.Println("Send stop signal to server")
		quit<-common.StopSignal
	}()

	<-quit
	log.Println("Watcher exits")
}
