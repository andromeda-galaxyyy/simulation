package main

import (
	"bufio"
	"chandler.com/gogen/utils"
	"debug/elf"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"strconv"
)

func main(){
	debug:=flag.Bool("debug",true,"Enable debug mode")


	id:=flag.Int("id",0,"self id")
	dstIdFn:=flag.String("dst_id","/home/stack/code/graduate/sim/system/traffic/gogen/test/0.hostid","destiantion id file")
	pktDir:=flag.String("pkts","/home/stack/code/graduate/sim/system/traffic/gogen/pkts/default","pkts dir")
	mtu:=flag.Int("mtu",1500,"Interface MTU")
	emptyPktSize:=flag.Int("emppkt",64,"Empty Layer4 Packet Size in bytes")
	interf:=flag.String("int","h0-eth0","Interface name")
	winSize:=flag.Int("ws",10,"Window size")
	controllerIP:=flag.String("cip","172.16.181.1","Controller ip")
	controllerSocketPort:=flag.Int("cport",1025,"Controller Socket Port")
	sleep:=flag.Bool("sleep",true,"whether sleep between packets")
	report:=flag.Bool("report",true,"whether report between packets")
	delay:=flag.Bool("delay",true,"whether delay before packet injection")
	delayTime:=flag.Int("delaytime",100,"delay time")
	flowType:=flag.Int("ftype",0,"Flow Type")

	enablePktLossStats:=flag.Bool("loss",false,"Whether enable pkt loss stats collection")
	pktLossDir:=flag.String("loss_dir","/tmp/txloss","Dir to store pkt loss stats")

	forceTarget:=flag.Bool("forcetarget",false,"Whether force target")
	target:=flag.Int("target",-1,"If enable force target,the target id")



	//dumb generator
	isDumb:=flag.Bool("dumb",false,"Whether use dumb generator")
	ipFile:=flag.String("ips","","IP file")
	macFile:=flag.String("macs","","MAC file")
	nFlows:=flag.Int("flows",10,"Number of flow")
	selfIp:=flag.String("selfip","","Self ip")
	selfMac:=flag.String("selfmac","","Self mac")


	flag.Parse()

	if !(*debug){
		fmt.Println("disable debug")
		log.SetOutput(ioutil.Discard)
	}

	fType= *flowType
	if fType>=4{
		log.Fatalf("Unsupported flow type %d\n",fType)
	}

	log.Printf("flow type %d",fType)

	if *forceTarget{
		log.Printf("Enable force target")
		if *target==-1{
			log.Fatalln("You must supply a target id")
		}else{
			log.Printf("Supplied target :%d",*target)
		}
	}


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
			FlowSizeInPacket: 10,
			Intf:             *interf,
		}
		dumb.Init()
		dumb.Start()
	}else{

		if *enablePktLossStats{
			log.Println("Enable pkt loss stats collection")
			if utils.DirExists(*pktLossDir){
				err=utils.RMDir(*pktLossDir)
				if err!=nil{
					log.Fatalf("Cannot remove pkt loss stats dir %s\n",*pktLossDir)
				}
				err=utils.CreateDir(*pktLossDir)
				if err!=nil{
					log.Fatalf("Cannot create pkt loss stats dir %s\n",*pktLossDir)
				}
			}

		}

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
			Debug: *debug,
			ForceTarget: *forceTarget,
			Target: *target,
			enablePktLossStats: *enablePktLossStats,
			pktLossDir: *pktLossDir,
		}

		generator.Init()
		err=generator.Start()
		if err!=nil{
			log.Fatalln(err)
		}
	}


}