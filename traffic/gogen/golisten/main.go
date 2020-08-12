package main

import (
	"chandler.com/gogen/utils"
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

	listenerID:=flag.Int("id",0,"Listener ID")
	intf:=flag.String("intf","h1-eth0","Interface to listen")
	nworker:=flag.Int("worker",16,"Number of listener workers")
	enableWorkers:=flag.Bool("enable_workers",true,"Whether enable multiple workers")
	srcSubnet:=flag.String("src","10.0.0.0/16","Source host subnet")
	dstSubnet:=flag.String("dst","10.0.0.0/16","Destination host subnet")

	srcHostIp:=flag.String("src_ips_file","","File which contains source host ip to be captured")
	//dstHostIp:=flag.String("dst_ips_file","","File which contains dst host ip to be captured")

	sportRange:=flag.String("srange","1500-65535","Source port range")
	dportRange:=flag.String("drange","1500-65535","Destination port range")


	delayBaseDir:=flag.String("delay_dir","/tmp/rxdelay","Base dir to store delay stats")
	pktLossBaseDir:=flag.String("loss_dir","/tmp/rxloss","Base dir to store loss stats")
	enableLossStats:=flag.Bool("loss",false,"Whether enable packet loss stats")
	items:=flag.Int64("items",20,"Number of items per file")


	flag.Parse()
	if *items<=0{
		log.Fatalf("Invalid args for items per file %d\n",items);
	}
	itemsPerFile=*items

	if *listenerID<0{
		log.Fatalf("Invalid listener id %d\n",*listenerID)
	}

	lid=*listenerID

	if !(*debug){
		log.SetOutput(ioutil.Discard)
	}

	if len(*srcHostIp)>0{
		fmt.Printf("This will overwrite src subnet %s \n",*srcSubnet)
		if !utils.FileExist(*srcHostIp){
			log.Fatalf("Source host ip file does not exsits,now remove %s\n",*srcHostIp)
		}
	}

	if utils.DirExists(*delayBaseDir){
		log.Printf("Base dir for delay stats %s exists,now remove\n",*delayBaseDir)
		err=utils.RMDir(*delayBaseDir)
		if err!=nil{
			log.Fatalf("Error when deleting dir %s\n",*delayBaseDir)
		}
	}
	enablePktLossStats=*enableLossStats
	if enablePktLossStats{
		log.Println("Listener:enable packet stats")
	}

	err=utils.CreateDir(*delayBaseDir)
	if err!=nil{
		log.Fatalf("Cannot create dir for delay stats %s\n",*delayBaseDir)
	}

	if utils.DirExists(*pktLossBaseDir){
		log.Printf("Base dir for pkt loss stats %s exists\n",*pktLossBaseDir)
		err=utils.RMDir(*pktLossBaseDir)
		if err!=nil{
			log.Fatalf("Error when deleting dir %s\n",*pktLossBaseDir)
		}
	}

	err=utils.CreateDir(*pktLossBaseDir)
	if err!=nil{
		log.Fatalf("Cannot create dir for pkt loss stats %s\n",*pktLossBaseDir)
	}




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
		SrcIPFile: *srcHostIp,
		DelayBaseDir: *delayBaseDir,
		PktLossDir: *pktLossBaseDir,

	}
	l.Init()
	l.Start()
}