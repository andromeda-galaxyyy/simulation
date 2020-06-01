package main

import (
	"chandler.com/gogen/utils"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"log"
	"net"
	"strconv"
	"strings"
	"time"
	"fmt"
	"math/rand"
)

type worker struct {
	g *Generator
	pktFile string
	lines []string
	handle *pcap.Handle
	dstIps []string
	dstMacs []string

	rawData []byte
	sentRecord *utils.IntSet
	buffer gopacket.SerializeBuffer
	flowId2Port map[int][2]int
	flowStats map[int]map[string][]float64

	ether *layers.Ethernet
	vlan *layers.Dot1Q
	ipv4 *layers.IPv4
	tcp *layers.TCP
	udp *layers.UDP
}

func (w *worker)Init()  {
	w.flowStats=make(map[int]map[string][]float64)
	w.sentRecord=&utils.IntSet{}
	w.buffer=gopacket.NewSerializeBuffer()
	w.flowId2Port=make(map[int][2]int)

	w.rawData=make([]byte,1600)

	w.vlan=&layers.Dot1Q{
		VLANIdentifier: 3,
		Type: layers.EthernetTypeIPv4,
	}
	w.ether= &layers.Ethernet{
		EthernetType: layers.EthernetTypeDot1Q,
	}
	w.ipv4= &layers.IPv4{
		Version:    4,   //uint8
		IHL:        5,   //uint8
		TOS:        0,   //uint8
		Id:         0,   //uint16
		Flags:      0,   //IPv4Flag
		FragOffset: 0,   //uint16
		TTL:        255, //uint8
	}
	w.tcp=&layers.TCP{}
	w.udp=&layers.UDP{}
}

func (w *worker)start()  {
	rand.Shuffle(len(w.dstIps), func(i, j int) {
		w.dstIps[i],w.dstIps[j]=w.dstIps[j],w.dstIps[i]
		w.dstMacs[i],w.dstMacs[j]=w.dstMacs[j],w.dstMacs[i]
	})
	nDsts:=len(w.dstMacs)

	//lines,err:= utils.ReadLines(w.pktFile)
	//log.Printf("#lines %d",len(lines))
	//if err!=nil{
	//	log.Fatalf("Error reading pkt file %s\n",w.pktFile)
	//}
	for _,line:=range w.lines{
		content:=strings.Split(line," ")
		if len(content)!=6{
			log.Fatalf("Invalid pkt file %s\n",w.pktFile)
		}
		toSleep,err:=strconv.ParseFloat(content[0],64)
		if toSleep<0 && int(toSleep)!=-1{
			log.Fatalln("Invalid sleep time")
		}
		if err!=nil{
			log.Fatalf("Invalid idt time in pkt file %s\n\n", w.pktFile)
		}
		size,err:=strconv.Atoi(content[1])
		if err!=nil{
			log.Fatalf("Invalid pkt size in pkt file %s\n\n", w.pktFile)
		}
		proto:=content[2]
		flowId,err:=strconv.Atoi(content[3])
		if err!=nil{
			log.Fatalf("Invalid flow id in pkt file %s\n\n", w.pktFile)
		}
		//todo tsDiffInFlow
		tsDiffInFlow,err:=strconv.ParseFloat(content[4],64)
		if tsDiffInFlow<0 && int(tsDiffInFlow)!=-1{
			log.Fatalln("Invalid ts diff in flow")
		}
		if err!=nil{
			log.Fatalf("Invalid ts diff in flow in pkt file %s\n", w.pktFile)
		}
		last,err:=strconv.ParseInt(content[5],10,64)
		if err!=nil{
			log.Fatalf("Invalid last payload indicator in pkt file %s\n",w.pktFile)
		}
		isLastL4Payload :=false
		if last>0{
			log.Printf("Flow %d finished\n",flowId)
			isLastL4Payload =true
		}

		dstIPStr:=w.dstIps[flowId%nDsts]
		dstIP:=net.ParseIP(dstIPStr)
		dstMAC,_:=net.ParseMAC(w.dstMacs[flowId%nDsts])

		//determine sport and dport
		srcPort:=-1
		dstPort:=-1
		if ports,exsits:=w.flowId2Port[flowId];exsits{
			srcPort=ports[0]
			dstPort=ports[1]
		}else{
			srcPort,dstPort=randomFlowIdToPort(flowId)
			w.flowId2Port[flowId]=[2]int{srcPort,dstPort}
		}

		ether.DstMAC=dstMAC
		ipv4.DstIP=dstIP

		addTs:=true

		if proto=="TCP"{
			tcp.SrcPort= layers.TCPPort(srcPort)
			tcp.DstPort= layers.TCPPort(dstPort)
			ipv4.Protocol=6
			err=send(w.handle,w.buffer, w.rawData,  size,payloadPerPacketSize, ether,vlan,ipv4,tcp,udp,true,addTs, isLastL4Payload)
			if err!=nil{
				log.Fatal(err)
			}
		}else{
			udp.SrcPort= layers.UDPPort(srcPort)
			udp.DstPort= layers.UDPPort(dstPort)
			ipv4.Protocol=17
			err=send(w.handle,w.buffer, w.rawData,  size,payloadPerPacketSize, ether,vlan,ipv4,tcp,udp,false,addTs, isLastL4Payload)
			//err=g.send(size,false,addTs,isLastL4Payload)
			if err!=nil{
				log.Fatal(err)
			}
		}


		_, exits := w.flowStats[flowId]
		if !exits {
			w.flowStats[flowId] = map[string][]float64{
				"pkt_size": make([]float64, 0),
				"idt":      make([]float64, 0),
			}
		}

		if w.g.Report {
			//collects
			if !w.sentRecord.Contains(flowId) {
				//log.Printf("hello : %d\n",len(g.flowStats[flowId]["pkt_size"]))
				//collect stats
				if len(w.flowStats[flowId]["pkt_size"]) == w.g.WinSize {
					//ok
					specifier := [5]string{
						fmt.Sprintf("%d", srcPort),
						fmt.Sprintf("%d", dstPort),
						w.g.ipStr,
						dstIPStr,
						proto,
					}
					stats := w.flowStats[flowId]
					go processFlowStats(w.g.ControllerIP, w.g.ControllerPort, specifier, utils.CopyMap(stats))
					delete(w.flowStats, flowId)
					w.sentRecord.Add(flowId)
				} else {
					w.flowStats[flowId]["pkt_size"] = append(w.flowStats[flowId]["pkt_size"], float64(size))
					w.flowStats[flowId]["idt"] = append(w.flowStats[flowId]["idt"], tsDiffInFlow)
				}
			}
		}

		if toSleep > 0 && w.g.Sleep {
			nano := int(toSleep)

			time.Sleep(time.Duration(nano) * time.Nanosecond)
		}
	}

}

