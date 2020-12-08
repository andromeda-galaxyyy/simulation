package main

import (
	"chandler.com/gogen/common"
	"context"
	"flag"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

var (
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

func setUpTelemetryRedisHandle(ip string,port int) error{
	telemetryHandle=redis.NewClient(&redis.Options{
		Addr:fmt.Sprintf("%s:%d", ip,port),
		DB:7,
	})
	_,err:=telemetryHandle.Ping(context.Background()).Result()
	if err!=nil{
		return err
	}
	return nil
}


func main()  {
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

	err=setUpFlowCounterReader(rip,rport)
	if err!=nil{
		log.Fatalf("Error init counter reader\n")
	}

	err=setUpTelemetryRedisHandle(rip, rport)
	if err!=nil{
		log.Fatalf("Error init network telemetry redis handle\n")
	}

	sigs:=make(chan os.Signal,1)
	signal.Notify(sigs,syscall.SIGINT,syscall.SIGTERM,syscall.SIGKILL)

	quit:=make(chan common.Signal,1)
	go func() {
		<-sigs
		log.Println("Stop requested")
		log.Println("Send stop signal to server")
		quit<-common.StopSignal
	}()

	router=gin.Default()
	router.GET("/delay",GetDelayBetween)
	router.GET("/loss",GetLossBetween)
	router.GET("/flowcounter",GetFlowCounter)
	router.GET("/telemetry/loss",TelemetryFunc(false))
	router.GET("/telemetry/delay",TelemetryFunc(true))

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
