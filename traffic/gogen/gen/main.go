package main
/**
 针对goroutine增多引起golang调度器cpu 占用增高的问题
reference：
1.http://xiaorui.cc/archives/6334
2. https://juejin.im/post/6844903887757901831
3. https://coralogix.com/log-analytics-blog/optimizing-a-golang-service-to-reduce-over-40-cpu/
 */

import (
	"bufio"
	"chandler.com/gogen/utils"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	_ "net/http/pprof"
	"os"
	"strconv"
)



func main(){
	//for profiling

	debug:=flag.Bool("debug",false,"Enable debug mode")


	id:=flag.Int("id",0,"self id")
	dstIdFn:=flag.String("dst_id","/home/stack/code/graduate/sim/system/traffic/gogen/test/0.hostid","destiantion id file")
	pktDir:=flag.String("pkts","/home/stack/code/graduate/sim/system/traffic/gogen/pkts/default","pkts dir")
	pktFn:=flag.String("pktsfn","","Specify a pkts file to use")
	mtu:=flag.Int("mtu",1500,"Interface MTU")
	emptyPktSize:=flag.Int("emppkt",64,"Empty Layer4 Packet Size in bytes")
	interf:=flag.String("int","h0-eth0","Interface name")
	winSize:=flag.Int("ws",10,"Window size")
	controllerIP:=flag.String("cip","172.16.181.1","Controller ip")
	controllerSocketPort:=flag.Int("cport",1025,"Controller Socket Port")

	redisIP:=flag.String("rip", "192.168.1.196","Redis IP address")
	redisPort:=flag.Int("rport",6379, "Redis Port")


	sleep:=flag.Bool("sleep",true,"whether sleep between packets")
	report:=flag.Bool("report",true,"whether report between packets")
	delay:=flag.Bool("delay",true,"whether delay before packet injection")
	delayTime:=flag.Int("delaytime",100,"delay time")
	flowType:=flag.Int("ftype",0,"Flow Type")

	enablePktLossStats:=flag.Bool("loss",true,"Whether enable pkt loss stats collection")
	pktLossDir:=flag.String("loss_dir","/tmp/txloss","Dir to store pkt loss stats")

	forceTarget:=flag.Bool("forcetarget",false,"Whether force target")
	target:=flag.Int("target",-1,"If enable force target,the target id")
	n_workers:=flag.Int("workers",1,"Number of coroutine to generate traffic")

	vlanid:=flag.Int("vlan",0,"Vlan id")



	//dumb generator
	isDumb:=flag.Bool("dumb",false,"Whether use dumb generator")
	ipFile:=flag.String("ips","","IP file")
	macFile:=flag.String("macs","","MAC file")
	nFlows:=flag.Int("flows",10,"Number of flow")
	selfIp:=flag.String("selfip","","Self ip")
	selfMac:=flag.String("selfmac","","Self mac")


	flag.Parse()
	vlanId=uint16(*vlanid)
	log.Printf("Specified vlan id %d\n",vlanId)
	if !(*debug){
		fmt.Println("disable debug")
		log.SetOutput(ioutil.Discard)
	}else{
		//debug
	//	trace.Start(os.Stderr)
	//	defer trace.Stop()
	//	go func() {
	//	log.Println(http.ListenAndServe("0.0.0.0:6060", nil))
	//}()
	}


	if len(*pktFn)>0{
		log.Printf("Specifed pkt file %s\n",*pktFn)
		if !utils.IsFile(*pktFn){
			log.Fatalf("Invalid pkt file %s\n",*pktFn)
		}
	}

	fType:= *flowType
	if fType>=4{
		log.Fatalf("Unsupported flow type %d\n",fType)
	}

	log.Printf("flow type %d",fType)

	if *forceTarget{
		log.Printf("Enable force target\n")
		if *target==-1{
			log.Fatalln("You must supply a target id")
		}else{
			log.Printf("Supplied target :%d\n",*target)
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
			if len(*pktLossDir)==0{
				log.Fatalf("You must provide a directory name\n")
				//log.Fatalf("Use default directory name\n");

			}
			if !utils.DirExists(*pktLossDir){
				err:=utils.CreateDir(*pktLossDir)
				if err!=nil{
					log.Fatalf("Cannot create pkt loss stats dir %s\n",*pktLossDir)
				}
			}
		}
		//


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

		//generator:=generator{
		//	ID:*id,
		//	MTU: *mtu,
		//	EmptySize: *emptyPktSize,
		//
		//	SelfID:        *id,
		//	DestinationIDs: dstIds,
		//	PktsDir:       *pktDir,
		//	Int: *interf,
		//	WinSize: *winSize,
		//	ControllerIP: *controllerIP,
		//	ControllerPort: *controllerSocketPort,
		//	Sleep: *sleep,
		//	Report: *report,
		//	Delay: *delay,
		//	DelayTime: *delayTime,
		//	Debug: *debug,
		//	ForceTarget: *forceTarget,
		//	Target: *target,
		//	enablePktLossStats: *enablePktLossStats,
		//	pktLossDir: *pktLossDir,
		//	fType: fType,
		//}
		//
		//generator.Init()
		//err=generator.Start()
		//if err!=nil{
		//	log.Fatalln(err)
		//}
		c:=&controller{
			id:                 *id,
			flowCounter:        0,
			numWorkers:        *n_workers,
			workers:            nil,
			mtu:                *mtu,
			emptySize:          *emptyPktSize,
			selfID:             utils.NowInMilli(),
			destinationIDs:     dstIds,
			pktsDir:            *pktDir,
			intf:               *interf,
			winSize:            *winSize,
			controllerIP:       *controllerIP,
			controllerPort:     *controllerSocketPort,
			sleep:              *sleep,
			report:             *report,
			delay:              *delay,
			delayDuration:      *delayTime,
			debug:              *debug,
			forceTarget:        *forceTarget,
			target:             *target,
			enablePktLossStats: *enablePktLossStats,
			pktLossDir:         *pktLossDir,
			flowType:           fType,
			specifiedPktFn: *pktFn,
			rip:*redisIP,
			rport:*redisPort,
		}


		err=c.Init()
		if err!=nil{
			log.Fatalln(err)
		}

		err=c.Start()
		if err!=nil{
			log.Fatalln(err)
		}
	}
}