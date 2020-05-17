package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
)





func main(){
	id:=flag.Int("id",0,"self id")
	dstIdFn:=flag.String("dst_id","/home/stack/code/graduate/sim/system/topo/files/0.hostids","destiantion id file")
	pktDir:=flag.String("pkts","/home/stack/code/graduate/sim/system/traffic/gogen/pkts","pkts dir")
	mtu:=flag.Int("mtu",1500,"Interface MTU")
	emptyPktSize:=flag.Int("emppkt",60,"Emptry Layer4 Packet Size in bytes")
	interf:=flag.String("int","h0-eth0","Interface name")
	winSize:=flag.Int("ws",10,"Window size")
	controllerIP:=flag.String("cip","172.16.181.1","Controller ip")
	controllerSocketPort:=flag.Int("cport",1025,"Controller Socket Port")
	sleep:=flag.Bool("sleep",true,"whether sleep between packets")
	report:=flag.Bool("report",true,"whether report between packets")
	delay:=flag.Bool("delay",true,"whether delay before packet injection")


	flag.Parse()

	if !FileExist(*dstIdFn){
		log.Fatal(fmt.Sprintf("File not exists %s\n", *dstIdFn))
	}
	if !DirExists(*pktDir){
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
	}
	generator.Init()
	err=generator.Start()
	if err!=nil{
		log.Fatalln(err)
	}
}