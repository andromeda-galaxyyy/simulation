package main

import (
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"io/ioutil"
	"log"
	"math/rand"
	"net"
	"path"
	"strconv"
	"strings"
	"time"
)

type Generator struct {
	ID int
	MTU int
	EmptySize int
	SelfID int
	DestinationIDs []int
	PktsDir string
	Int string
	WinSize int

	rawData []byte
	handle *pcap.Handle
	timeout time.Duration
	options gopacket.SerializeOptions
	flowStats map[string] []float32
    sentRecord IntSet
	//destinationIPs []string
	//destinationMACs []string

}

var (
	ether *layers.Ethernet
	ipv4 *layers.IPv4
	tcp *layers.TCP
	udp *layers.UDP
)

func Init()  {
	ether= &layers.Ethernet{
		EthernetType: 0x800,
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
}


func (g *Generator)Start() (err error) {
	log.Printf("Start to generate")
	nDsts:=len(g.DestinationIDs)
	//init handler
	handle,err:=pcap.OpenLive(g.Int,1024,false,g.timeout)
	if err!=nil{
		log.Fatalf("Cannot open device %s\n",g.Int)
	}
	defer handle.Close()
	g.handle=handle
	g.rawData=make([]byte,1600)

	//self ip and mac
	ipStr,err:=GenerateIP(g.ID)
	if err!=nil{
		log.Fatalf("Invalid generator id %d\n",g.ID)
	}
	ip:=net.ParseIP(ipStr)
	ipv4.SrcIP=ip
	macStr,err:=GenerateMAC(g.ID)
	mac,_:=net.ParseMAC(macStr)
	ether.SrcMAC=mac


	if err!=nil{
		log.Fatalf("Invalid generator id %d\n",g.ID)
	}

	DstIPs:=make([]string,0)
	DstMACs:=make([]string,0)
	for _,dstId:=range g.DestinationIDs{
		ip,err:=GenerateIP(dstId)
		if err!=nil{
			log.Fatalf("Generator: %d Error when generate ip for %d",g.ID,dstId)
		}
		DstIPs=append(DstIPs,ip)
		mac,err:=GenerateMAC(dstId)
		if err!=nil{
			log.Fatalf("Generator: %d Error when generate mac for %d",g.ID,dstId)
		}
		DstMACs=append(DstMACs,mac)

	}

	//count files
	pktFileCount:=0
	files,err:=ioutil.ReadDir(g.PktsDir)
	pktFns:=make([]string,0)
	if err!=nil{
		return err
	}
	for _,f:=range files{
		if strings.Contains(f.Name(),"pkts"){
			pktFileCount++
			pktFns=append(pktFns,f.Name())
		}
	}
	//shuffle
	rand.Seed(time.Now().UnixNano())
	rand.Shuffle(len(pktFns), func(i, j int) {
		pktFns[i],pktFns[j]=pktFns[j],pktFns[i]
	})

	//尽量减少端口冲突
	portSegLen:=(66635-1500)/pktFileCount
	pktFileIdx:=0

	for{
		g.reset()
		//#read pkt file
		pktFile:=path.Join(g.PktsDir,pktFns[pktFileIdx])
		lines,err:=ReadLines(pktFile)
		if err!=nil{
			log.Fatalf("Error reading pkt file %s\n",pktFile)
		}
		for _,line:=range lines{
			content:=strings.Split(line," ")
			if len(content)!=5{
				log.Fatalf("Invalid pkt file %s\n",pktFile)
			}
			//todo to_sleep
			//toSleep,err:=strconv.ParseFloat(content[0],32)
			if err!=nil{
				log.Printf("Invalid idt time in pkt file %s\n\n", pktFile)
				break
			}
			size,err:=strconv.Atoi(content[1])
			if err!=nil{
				log.Printf("Invalid pkt size in pkt file %s\n\n", pktFile)
				break
			}
			proto:=content[2]
			flowId,err:=strconv.Atoi(content[3])
			if err!=nil{
				log.Printf("Invalid flow id in pkt file %s\n\n", pktFile)
				break
			}
			//todo tsDiffInFlow
			//tsDiffInFlow,err:=strconv.Atoi(content[4])
			if err!=nil{
				log.Printf("Invalid ts diff in flow in pkt file %s\n\n", pktFile)
				break
			}

			dstIP:=net.ParseIP(DstIPs[flowId%nDsts])
			dstMAC,_:=net.ParseMAC(DstMACs[flowId%nDsts])

			srcPort:=1500+(pktFileIdx*portSegLen)+flowId%portSegLen
			dstPort:=srcPort
			ether.DstMAC=dstMAC
			ipv4.DstIP=dstIP

			if proto=="TCP"{
				tcp.SrcPort= layers.TCPPort(srcPort)
				tcp.DstPort= layers.TCPPort(dstPort)
				_=g.send(size,ether,ipv4,tcp,nil,true)
			}else{
				udp.SrcPort= layers.UDPPort(srcPort)
				udp.DstPort= layers.UDPPort(dstPort)
				_=g.send(size,ether,ipv4,nil,udp,false)
			}
			//time.Sleep(time.Duration())
		}
	}

}

func (g *Generator) send(payloadSize int,ether *layers.Ethernet,ip *layers.IPv4,tcp *layers.TCP,udp *layers.UDP,isTCP bool) (err error){
	buffer:=gopacket.NewSerializeBuffer()
	if isTCP{
		err=gopacket.SerializeLayers(buffer,g.options,ether,ip,tcp,gopacket.Payload(g.rawData[:payloadSize]))
		if err!=nil{
			return err
		}
	}else{
		err=gopacket.SerializeLayers(buffer,g.options,ether,ip,udp,gopacket.Payload(g.rawData[:payloadSize]))
		if err!=nil{
			return err
		}
	}
	return nil
}

func (g *Generator)reset(){
	g.sentRecord.init()
	g.flowStats=make(map[string][]float32)
}

