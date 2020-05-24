package main

import (
	"chandler.com/gogen/utils"
	"fmt"
	"github.com/google/gopacket/pcap"
	"log"
	"math/rand"
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
}

func (g *DumbGenerator)Init()  {
	rand.Seed(time.Now().UnixNano())
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
				dmac:=macs[flowId%nTarget]
				dip:=ips[flowId%nTarget]
				specifier:=[5]string{
					sport,dport,g.SelfIP,dip,"TCP",
				}
				err:=utils.Send(specifier,g.SelfMAC,dmac,1000,g.handle)
				if err!=nil{
					log.Fatalln(err)
				}
				time.Sleep(100*time.Nanosecond)
				time.Sleep(time.Nanosecond*time.Duration(sleepInNano))
			}
		}
		//all the flow has finished
	}
}

