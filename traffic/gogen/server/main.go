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
	"path/filepath"
	"strings"
	"syscall"
	"time"
)

var (
	defaultDirs string
	rport int=6379
	rip string="localhost"
)

func setUpFlowCounterReader(ip string,port int)error  {
	counterReader=common.NewDefaultCounterReader(ip,port)
	err:=counterReader.Init()
	return err

}


func setUpRedisHandle(ip string,port int) error  {
	ctx:=context.Background()
	delayHandle0 =redis.NewClient(&redis.Options{
		Addr:fmt.Sprintf("%s:%d",ip,port),
		Password: "",
		DB:0,
	})
	_,err:= delayHandle0.Ping(ctx).Result()
	if err!=nil{
		return err
	}

	delayHandle1 =redis.NewClient(&redis.Options{
		Addr:fmt.Sprintf("%s:%d",ip,port),
		Password: "",
		DB:1,
	})
	_,err= delayHandle1.Ping(ctx).Result()
	if err!=nil{
		return err
	}

	 lossHandle0=redis.NewClient(&redis.Options{
		Addr:fmt.Sprintf("%s:%d",ip,port),
		Password: "",
		DB:2,
	})
	_,err= lossHandle0.Ping(ctx).Result()
	if err!=nil{
		return err
	}

	lossHandle1=redis.NewClient(&redis.Options{
		Addr:fmt.Sprintf("%s:%d",ip,port),
		Password: "",
		DB:3,
	})
	_,err= lossHandle1.Ping(ctx).Result()
	if err!=nil{
		return err
	}
	return nil
}


func main()  {
	base_dir :=flag.String("base","/tmp/listener_log","Base directory to watch")
	serverPort:=flag.Int("port",10086,"Server listening port")
	redisPort:=flag.Int("rport",6379,"Redis instance port")
	redisIp:=flag.String("rip","10.211.55.2","Redis instance ip")
	dirs:=flag.String("dirs","/tmp/rxloss,/tmp/rxdelay","Directory to watch")

	flag.Parse()
	rport=*redisPort
	rip=*redisIp
	err:=setUpRedisHandle(rip,rport)
	if err!=nil{
		log.Fatalf("Cannot connect to redis instance %s:%d",rip,rport)
	}

	err=setUpFlowCounterReader(rip,rport)
	if err!=nil{
		log.Fatalf("Error init counter reader\n")
	}
	
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

	router=gin.Default()
	router.GET("/delay",GetDelayBetween)
	router.GET("/loss",GetLossBetween)
	router.GET("/flowcounter",GetFlowCounter)

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
