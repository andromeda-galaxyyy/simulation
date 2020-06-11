package main

import (
	"chandler.com/gogen/utils"
	"fmt"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"log"
	"math/rand"
	"net"
	"strconv"
	"time"
)


type DumbGenerator struct {
	//MB/s
	Speed int64
	IPFile string
	MACFile string
	SelfIP string
	SelfMAC string
	rawBytes []byte
	NFlows int
	FlowSizeInPacket int64
	Intf string
	handle *pcap.Handle
	buffer gopacket.SerializeBuffer
}

func (g *DumbGenerator)Init()  {
	g.buffer=gopacket.NewSerializeBuffer()
	g.rawBytes=make([]byte,1600)
	rand.Seed(time.Now().UnixNano())
	vlan=&layers.Dot1Q{
		VLANIdentifier: 3,
		Type: layers.EthernetTypeIPv4,
	}
	ether= &layers.Ethernet{
		EthernetType: layers.EthernetTypeDot1Q,
	}
	ipv4= &layers.IPv4{
		Version:    4,   //uint8
		IHL:        5,   //uint8
		TOS:        0,   //uint8
		Id:         0,   //uint16
		Flags:      0,   //IPv4Flag
		FragOffset: 0,   //uint16
		TTL:        255, //uint8
	}
	tcp=&layers.TCP{}
	udp=&layers.UDP{}
	options.FixLengths=true

}

func (g *DumbGenerator) Start(){
	handle,err:= pcap.OpenLive(g.Intf, 1024, false, 30*time.Second)
	if err!=nil{
		log.Fatalf("Cannot open device %s\n",g.Intf)
	}
	defer handle.Close()
	g.handle=handle
	ips,err:=utils.ReadLines(g.IPFile)
	if err!=nil{
		log.Fatal(err)
	}
	macs,err:=utils.ReadLines(g.MACFile)
	if err!=nil{
		log.Fatal(err)
	}
	if len(ips)!=len(macs){
		log.Fatalln("Size of ip file and mac file cannot match")
	}
	nTarget:=len(ips)

	sleepInNano:=int64(float64(1)/float64(g.Speed)*1000000)
	log.Printf("Sleep time %d\n",sleepInNano)
	for{
		rand.Shuffle(len(ips), func(i, j int) {
			ips[i],ips[j]=ips[j],ips[i]
			macs[i],macs[j]=macs[j],macs[i]
		})
		for i:=int64(0);i<g.FlowSizeInPacket;i++{
			for flowId:=0;flowId<g.NFlows;flowId++{
				sport:=fmt.Sprintf("%d",flowId%(65535-1500)+1500)
				dport:=fmt.Sprintf("%d",flowId%(65535-1500)+1500)
				sport_,err:=strconv.Atoi(sport)
				if err!=nil{
					log.Fatalf("Invalid source port %s\n",sport)
				}
				dport_,err:=strconv.Atoi(dport)
				if err!=nil{
					log.Fatalf("Invalid dst port %s\n",dport)
				}
				tcp.DstPort=layers.TCPPort(dport_)
				tcp.SrcPort=layers.TCPPort(sport_)

				dmac:=macs[flowId%nTarget]
				dmac_,_:=net.ParseMAC(dmac)
				smac_,_:=net.ParseMAC(g.SelfMAC)
				ether.DstMAC=dmac_
				ether.SrcMAC=smac_


				dip:=ips[flowId%nTarget]
				ipv4.SrcIP=net.ParseIP(g.SelfIP)
				ipv4.DstIP=net.ParseIP(dip)
				ipv4.Protocol=6

				lastPkt:=false
				if i==g.FlowSizeInPacket-1{
				 lastPkt=true
				}

				err=send(handle,g.buffer,g.rawBytes,1000,1200,ether,vlan,ipv4,tcp,udp,true,true,lastPkt)
				if err!=nil{
					log.Fatalln(err)
				}
				time.Sleep(100*time.Millisecond)
				//time.Sleep(time.Nanosecond*time.Duration(sleepInNano))
			}
		}
		//all the flow has finished
	}
}

