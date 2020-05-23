package main

import (
	"chandler.com/gogen/utils"
	"github.com/google/gopacket/pcap"
	"log"
	"testing"
	"time"
)
var (
	srcMacStr string
	dstMacStr string
	srcIpStr  string
	dstIpStr  string
	sp        int
	dp        int
)

func TestListener_Start(t *testing.T) {
	specifier:=[5]string{
		"1500",
		"3000",
		"172.16.181.1",
		"172.16.181.151",
		"TCP",
	}
	srcMac:="00:50:56:c0:00:08"
	dstMac:="00:0c:29:1d:18:6e"
	intf:="vmnet8"
	handle,err:=pcap.OpenLive(intf,1024,false,30*time.Second)
	if err!=nil{
		log.Fatalf("Cannot open device %s\n",intf)
	}
	defer handle.Close()
	err=utils.Send(specifier,srcMac,dstMac,1000,handle)
	if err!=nil{
		log.Fatalln(err)
	}
}