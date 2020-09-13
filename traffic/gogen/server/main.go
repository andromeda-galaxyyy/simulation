package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"context"
	"flag"
	"github.com/gin-gonic/gin"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"
)

func main()  {
	ds:=flag.String("dirs","/tmp/foo","Directory to watch")
	flag.Parse()
	dd:=strings.Split(*ds," ")
	for _,d:=range dd{
		if !utils.IsDir(d){
			log.Fatalf("%s is not directory\n",d)
		}
	}


	delayChan:=make(chan string,10240)
	lossChan:=make(chan string,10240)
	fileChan:=make(chan string,10240)
	doneChanToWatcher :=make(chan common.Signal,1)
	doneChanToWriter:=make(chan common.Signal,1)

	sigs:=make(chan os.Signal,1)
	signal.Notify(sigs,syscall.SIGINT,syscall.SIGTERM,syscall.SIGKILL)




	dbWriter:= NewMongoWriter("10.211.55.2",27017)
	dbWriter.delayChan=delayChan
	dbWriter.lossChan=lossChan
	dbWriter.fileChan=fileChan
	dbWriter.done=doneChanToWriter
	dbWriter.initiator=DefaultInitiator

	dbWriter.Init()
	go dbWriter.Start()

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
	//start server
	router=gin.Default()
	router.GET("/", func(context *gin.Context) {
		context.String(http.StatusOK,"Hello world")
	})

	router.GET("/helloworld",GinHelloWorld)

	server:=&http.Server{
		Addr: ":8083",
		Handler: router,
	}
	go func() {
		if err:=server.ListenAndServe();err!=nil{
			log.Fatalln("Cannot start server")
		}
		log.Println("server started")
	}()

	<-quit
	log.Println("Server stop requested")
	ctx,cancel:=context.WithTimeout(context.Background(),5*time.Second)
	defer cancel()
	if err:=server.Shutdown(ctx);err!=nil{
		log.Fatalln("Cannot shutdown server",err)
	}
	log.Println("Server shutdown now")
}
