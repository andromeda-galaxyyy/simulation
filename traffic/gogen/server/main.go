package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"context"
	"flag"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"
)

var (
	defaultDirs string
	rport int=6379
	rip string="localhost"
)

func setUpRedisHandle(ip string,port int) error  {

	ctx:=context.Background()
	delayHandle =redis.NewClient(&redis.Options{
		Addr:fmt.Sprintf("%s:%d",ip,port),
		Password: "",
		DB:0,
	})
	_,err:=delayHandle.Ping(ctx).Result()
	if err!=nil{
		return err
	}
	lossHandle=redis.NewClient(&redis.Options{
		Addr:fmt.Sprintf("%s:%d",ip,port),
		Password: "",
		DB:1,
	})
	_,err=delayHandle.Ping(ctx).Result()
	if err!=nil{
		return err
	}
	return nil
}


func main()  {
	ds:=flag.String("dirs","/tmp/rxdelay","Directory to watch")
	serverPort:=flag.Int("port",10086,"Server listening port")
	redisPort:=flag.Int("rport",6379,"Redis instance port")
	redisIp:=flag.String("rip","10.211.55.2","Redis instance ip")

	flag.Parse()
	rport=*redisPort
	rip=*redisIp
	err:=setUpRedisHandle(rip,rport)
	if err!=nil{
		log.Fatalf("Cannot connect to redis instance %s:%d",rip,rport)
	}

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


	redisWriter := NewDefaultRedisWriter(*redisIp,*redisPort)
	redisWriter.delayChan=delayChan
	redisWriter.lossChan=lossChan
	redisWriter.fileChan=fileChan
	redisWriter.doneChan=doneChanToWriter

	err=redisWriter.Init()
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
	//start server
	router=gin.Default()
	router.GET("/", func(context *gin.Context) {
		context.String(http.StatusOK,"Hello world")
	})

	router.GET("/helloworld",GinHelloWorld)

	server:=&http.Server{
		Addr: fmt.Sprintf(":%d",*serverPort),
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
