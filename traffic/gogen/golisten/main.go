package main

import (
	"errors"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"strconv"
	"strings"
)
var (
	err error
)

func main()  {
	debug:=flag.Bool("debug",true,"enable debug mode")
	if !(*debug){
		log.SetOutput(ioutil.Discard)
	}

	intf:=flag.String("intf","ens33","Interface to listen")
	nworker:=flag.Int("worker",8,"Number of listener workers")
	enableWorkers:=flag.Bool("enable_workers",true,"Whether enable multiple workers")
	srcSubnet:=flag.String("src","10.0.0.0/24","Source host subnet")
	dstSubnet:=flag.String("dst","10.0.0.0/24","Destination host subnet")
	sportRange:=flag.String("srange","1500-65535","Source port range")
	dportRange:=flag.String("drange","1500-65535","Destination port range")

	flowStatsBaseDir:=flag.String("dir","/tmp/log","Flow stats base dir")


	flag.Parse()
	if *enableWorkers&&!(*nworker>0){
		err=errors.New(fmt.Sprintf("Invalid number of worker: %d",*nworker))
	}

	sports:=strings.Split(*sportRange,"-")
	if len(sports)!=2{
		err=errors.New(fmt.Sprintf("Invalid sport range: %s",*sportRange))
		log.Fatalln(err)
	}

	sportLower,err:=strconv.Atoi(sports[0])
	if err!=nil{
		err=errors.New(fmt.Sprintf("Invalid sport range: %s",*sportRange))
		log.Fatalln(err)
	}
	sportUpper,err:=strconv.Atoi(sports[1])
	if err!=nil{
		err=errors.New(fmt.Sprintf("Invalid sport range: %s",*sportRange))
		log.Fatalln(err)
	}

	dports:=strings.Split(*dportRange,"-")
	if len(dports)!=2{
		err=errors.New(fmt.Sprintf("Invalid dport range %s",*dportRange))
		log.Fatalln(err)
	}

	dportLower,err:=strconv.Atoi(dports[0])
	if err!=nil{
		err=errors.New(fmt.Sprintf("Invalid dport range %s",*dportRange))
		log.Fatalln(err)
	}
	dportUpper,err:=strconv.Atoi(dports[1])
	if err!=nil{
		err=errors.New(fmt.Sprintf("Invalid dport range %s",*dportRange))
		log.Fatalln(err)
	}



	l:=&Listener{
		Intf:          *intf,
		NWorker:       *nworker,
		EnableWorkers: *enableWorkers,
		SrcSubnet:     *srcSubnet,
		DstSubnet:     *dstSubnet,
		SrcPortUpper:  sportUpper,
		SrcPortLower:  sportLower,
		DstPortLower:  dportLower,
		DstPortUpper:  dportUpper,

		WriterBaseDir: *flowStatsBaseDir,
	}
	l.Init()
	l.Start()
}