package main

import (
	"fmt"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"log"
	"strconv"
	"time"
)

func init()  {

}

var (
	snapshot_len int32 =1024
	promiscuous          = false
	timeout      =30*time.Second
	specifier    =[5]string{}
	sport,dport,sip,dip,proto string
)

type Listener struct {
	Intf string
	NWorker int
	EnableWorkers bool
	SrcPortLower int
	SrcPortUppper int
	DstPortLower int
	DstPortUpper int
	SrcSubnet string
	DstSubnet string

	workers []*Worker
	packetChannels []chan gopacket.Packet
}

type Worker struct {
	//观测窗口大小
	WinSize int
	//some private fields
}

func printPacket(packet *gopacket.Packet)  {
	//sport,dport,sip,dip,proto
	ipLayer:=(*packet).Layer(layers.LayerTypeIPv4)
	if ipLayer ==nil{
		return
	}

	ip,_:=ipLayer.(*layers.IPv4)
	sip=ip.SrcIP.String()
	dip=ip.DstIP.String()

	tcpLayer :=(*packet).Layer(layers.LayerTypeTCP)
	if tcpLayer !=nil{
		tcp,_:= tcpLayer.(*layers.TCP)
		sport=strconv.Itoa(int(tcp.SrcPort))
		dport=strconv.Itoa(int(tcp.DstPort))
		specifier[0]=sport
		specifier[1]=dport
		specifier[2]=sip
		specifier[3]=dip
		specifier[4]="TCP"
		//copied
		processStats(specifier,0)
	}
	udpLayer:=(*packet).Layer(layers.LayerTypeUDP)
	if udpLayer!=nil{
		udp,_:= udpLayer.(*layers.UDP)
		sport=strconv.Itoa(int(udp.SrcPort))
		dport=strconv.Itoa(int(udp.DstPort))
		specifier[0]=sport
		specifier[1]=dport
		specifier[2]=sip
		specifier[3]=dip
		specifier[4]="UDP"
		//copied
		processStats(specifier,0)
	}
}

func (w *Worker)start(packetChannel chan gopacket.Packet)  {
	for packet:=range packetChannel{
		printPacket(&packet)
	}
}

func processStats(specifier [5]string,time int64)  {
	fmt.Printf("sport %s,dport %s,sip %s,dip %s,proto %s\n",specifier[0],specifier[1],specifier[2],specifier[3],specifier[4])
}

func (l *Listener)getFilter() (filter string){
	filter=fmt.Sprintf("src net %s && dst net %s && src portrange %d-%d && dst portrange %d-%d",
	l.SrcSubnet,
	l.DstSubnet,
	l.SrcPortLower,
	l.SrcPortUppper,
	l.DstPortLower,
	l.DstPortUpper,
	)
	return filter
}

func (l *Listener)Start()  {
	log.Printf("Listener start")
	handle,err:=pcap.OpenLive(l.Intf,snapshot_len,promiscuous,pcap.BlockForever)
	if err!=nil{
		log.Fatalf("Cannot open %s\n",l.Intf)
	}
	defer handle.Close()
	//set filter
	filter:=l.getFilter()
	log.Printf("Filter:%s\n",filter)

	err=handle.SetBPFFilter(filter)
	if err!=nil{
		log.Fatalln(err)
	}
	packetSource:=gopacket.NewPacketSource(handle,handle.LinkType())
	//todo set filter
	if l.EnableWorkers{
		log.Println("Dispatching")
		for packet:=range packetSource.Packets(){
			if net:=packet.NetworkLayer();net!=nil{
				l.packetChannels[int(net.NetworkFlow().FastHash())&(l.NWorker-1)]<-packet
			}
		}
	}else{
		//disable worker
		for packet:=range packetSource.Packets(){
			printPacket(&packet)
		}
	}

}

func (l *Listener)Init()  {
	var roundUp = func(n int) int {
		n=n-1
		for;n&(n-1)!=0;{
			n=n&(n-1)
		}
		return n*2
	}
	//init channel
	if l.EnableWorkers{

		l.NWorker=roundUp(l.NWorker)
		log.Printf("Listener get workers enabled, #workers: %d\n",l.NWorker)
		l.workers=make([]*Worker,l.NWorker)
		l.packetChannels=make([]chan gopacket.Packet,l.NWorker)
		//TODO win size
		for i:=0;i<l.NWorker;i++{
			l.workers=append(l.workers,&Worker{WinSize: 8})
			l.packetChannels[i]=make(chan gopacket.Packet,1024)
		}
		for i:=0;i<l.NWorker;i++{
			go l.workers[i].start(l.packetChannels[i])
		}
	}


}