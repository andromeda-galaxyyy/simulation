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

func send_tcp(data []byte,
	tcpLayer *layers.TCP,
	ipv4Layer *layers.IPv4,
	ethernetLayer *layers.Ethernet) (err error) {

	buffer := gopacket.NewSerializeBuffer()
	gopacket.SerializeLayers(buffer, options,
		tcpLayer,
		gopacket.Payload(data),
	)
	return send_ipv4(buffer.Bytes(), ipv4Layer, ethernetLayer)
}

func send_ipv4(data []byte,
	ipv4Layer *layers.IPv4,
	ethernetLayer *layers.Ethernet) (err error) {

	buffer_ipv4 := gopacket.NewSerializeBuffer()
	gopacket.SerializeLayers(buffer_ipv4, options,
		ipv4Layer,
		gopacket.Payload(data),
	)
	return send_ethernet(buffer_ipv4.Bytes(), ethernetLayer)
}

func send_ethernet(data []byte,
	ethernetLayer *layers.Ethernet) (err error) {

	buffer_ethernet := gopacket.NewSerializeBuffer()
	gopacket.SerializeLayers(buffer_ethernet, options,
		ethernetLayer,
		gopacket.Payload(data),
	)
	err = handle.WritePacketData(buffer_ethernet.Bytes())
	if err != nil {
		log.Fatal(err)
	}
	return err
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
	//sport,err:=strconv.Atoi(specifier[0])
	//if err!=nil{
	//	log.Fatalln(err)
	//}
	//dport,err:=strconv.Atoi(specifier[1])
	//if err!=nil{
	//	log.Fatalln(err)
	//}
	//sip:=specifier[2]
	//dip:=specifier[3]
	//proto:=specifier[4]
	//tcp:= proto=="TCP"
	//srcMac,_:=net.ParseMAC(smac)
	//dstMac,_:=net.ParseMAC(dmac)
	//etherLayer.SrcMAC=srcMac
	//etherLayer.DstMAC=dstMac
	//
	//ipv4Layer.SrcIP=net.ParseIP(sip)
	//ipv4Layer.DstIP=net.ParseIP(dip)
	//if tcp{
	//	ipv4Layer.Protocol=6
	//	tcpLayer.SrcPort=layers.TCPPort(sport)
	//	tcpLayer.DstPort=layers.TCPPort(dport)
	//
	//}else{
	//	ipv4Layer.Protocol=17
	//	udpLayer.SrcPort=layers.UDPPort(sport)
	//	udpLayer.DstPort=layers.UDPPort(dport)
	//}
	//send_tcp([]byte{1,2,3,4},tcpLayer,ipv4Layer,etherLayer)
}