package main

import (
	"bufio"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strconv"
	"chandler.com/gogen/utils"
)





func main(){
	debug:=flag.Bool("debug",true,"Enable debug mode")
	if !(*debug){
		log.SetOutput(ioutil.Discard)
	}

	id:=flag.Int("id",0,"self id")
	dstIdFn:=flag.String("dst_id","/home/stack/code/graduate/sim/system/topo/files/0.hostids","destiantion id file")
	pktDir:=flag.String("pkts","/home/stack/code/graduate/sim/system/traffic/gogen/pkts","pkts dir")
	mtu:=flag.Int("mtu",1500,"Interface MTU")
	emptyPktSize:=flag.Int("emppkt",64,"Empty Layer4 Packet Size in bytes")
	interf:=flag.String("int","h0-eth0","Interface name")
	winSize:=flag.Int("ws",10,"Window size")
	controllerIP:=flag.String("cip","172.16.181.1","Controller ip")
	controllerSocketPort:=flag.Int("cport",1025,"Controller Socket Port")
	sleep:=flag.Bool("sleep",true,"whether sleep between packets")
	report:=flag.Bool("report",true,"whether report between packets")
	delay:=flag.Bool("delay",true,"whether delay before packet injection")
	delayTime:=flag.Int("delaytime",30,"delay time")



	//dumb generator
	isDumb:=flag.Bool("dumb",false,"Whether use dumb generator")
	ipFile:=flag.String("ips","","IP file")
	macFile:=flag.String("macs","","MAC file")
	nFlows:=flag.Int("flows",100,"Number of flow")
	selfIp:=flag.String("selfip","","Self ip")
	selfMac:=flag.String("selfmac","","Self mac")


	flag.Parse()
	if *isDumb{
		log.Println("Use dumb generator")
		if !utils.FileExist(*ipFile){
			log.Fatalf("ip file does not exsit %s\n",*ipFile)
		}
		if !utils.FileExist(*macFile){
			log.Fatalf("mac file does not exsit %s\n",*macFile)
		}
		dumb:=DumbGenerator{
			Speed:            100,
			IPFile:           *ipFile,
			MACFile:          *macFile,
			SelfIP:           *selfIp,
			SelfMAC:          *selfMac,
			NFlows:           *nFlows,
			FlowSizeInPacket: 1000,
			Intf:             *interf,
		}
		dumb.Init()
		dumb.Start()
	}else{
		if !utils.FileExist(*dstIdFn){
			log.Fatal(fmt.Sprintf("File not exists %s\n", *dstIdFn))
		}
		if !utils.DirExists(*pktDir){
			log.Fatal(fmt.Sprintf("Dir not exists %s\n", *pktDir))
		}
		dstIds:=make([]int,0)

		fp,err:=os.Open(*dstIdFn)
		if err!=nil{
			log.Fatal(err)
		}
		defer fp.Close()

		scanner:=bufio.NewScanner(fp)
		for scanner.Scan(){
			res,err:=strconv.Atoi(scanner.Text())
			if err!=nil{
				log.Fatal("Invalid destination id file")
			}
			dstIds=append(dstIds,res)
		}
		log.Println(fmt.Sprintf("#destination id file %d",len(dstIds)))

		generator:=Generator{
			ID:*id,
			MTU: *mtu,
			EmptySize: *emptyPktSize,
			SelfID:        *id,
			DestinationIDs: dstIds,
			PktsDir:       *pktDir,
			Int: *interf,
			WinSize: *winSize,
			ControllerIP: *controllerIP,
			ControllerPort: *controllerSocketPort,
			Sleep: *sleep,
			Report: *report,
			Delay: *delay,
			DelayTime: *delayTime,
		}
		generator.Init()
		err=generator.Start()
		if err!=nil{
			log.Fatalln(err)
		}
	}


}