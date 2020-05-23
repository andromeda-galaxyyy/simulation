package main

import (
	"chandler.com/gogen/utils"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
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
	options gopacket.SerializeOptions
	handle *pcap.Handle
	rawBytes       [] byte
	buffer         gopacket.SerializeBuffer
	etherLayer     *layers.Ethernet
	ipv4Layer      *layers.IPv4
	tcpLayer       *layers.TCP
	udpLayer       *layers.UDP
	defaultOptions *gopacket.SerializeOptions
)


func Init()  {
	buffer=gopacket.NewSerializeBuffer()
	defaultOptions=&gopacket.SerializeOptions{}
	etherLayer = &layers.Ethernet{
		EthernetType: 0x800,
	}
	ipv4Layer = &layers.IPv4{
		Version:    4,   //uint8
		IHL:        5,   //uint8
		TOS:        0,   //uint8
		Id:         0,   //uint16
		Flags:      0,   //IPv4Flag
		FragOffset: 0,   //uint16
		TTL:        255, //uint8
	}
	tcpLayer=&layers.TCP{}
	udpLayer=&layers.UDP{}
	rawBytes=make([]byte,1600)
}


func TestListener_Start(t *testing.T) {
	//Init()
	specifier:=[5]string{
		"1500",
		"3000",
		"172.16.181.1",
		"172.16.181.151",
		"TCP",
	}
	smac:="00:50:56:c0:00:08"
	dmac:="00:0c:29:1d:18:6e"
	intf:="vmnet8"
	handle,err:=pcap.OpenLive(intf,1024,false,30*time.Second)
	if err!=nil{
		log.Fatalf("Cannot open device %s\n",intf)
	}

	defer handle.Close()
	err=utils.Send(specifier,smac,dmac,1000,handle)
	if err!=nil{
		log.Fatal(err)
	}

}