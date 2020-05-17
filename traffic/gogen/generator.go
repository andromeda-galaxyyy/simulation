package main

import (
	"fmt"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"gonum.org/v1/gonum/stat"
	"io/ioutil"
	"log"
	"math"
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
	ControllerIP string
	ControllerPort int
	Sleep bool
	Report bool
	Delay bool

	rawData []byte
	handle *pcap.Handle
	timeout time.Duration
	options gopacket.SerializeOptions
	//flow-id ---> {pkt_size:[],idt:[]}
	flowStats map[int]map[string][]float64
    sentRecord *IntSet
	buffer gopacket.SerializeBuffer
	flowId2Port map[int][2]int

}

var (
	ether *layers.Ethernet
	ipv4 *layers.IPv4
	tcp *layers.TCP
	udp *layers.UDP
)




func init()  {
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

func processStats(nums []float64) (min,max,mean float64)  {
	min=math.MaxFloat64
	max=-1
	valid_count:=0
	sum:=float64(0)
	for _,v:=range nums{
		if v<0{
			continue
		}
		valid_count++
		sum+=v
		if v>max{
			max=v
		}
		if v<min{
			min=v
		}
	}
	return min,max, sum/float64(valid_count)
}

func processFlowStats(ip string,port int,specifier [5]string,stats map[string][]float64){
	pktSizes:=stats["pkt_size"]
	idts:=stats["idt"]
	minPktSize,maxPktSize,meanPktSize:=processStats(pktSizes)
	stdvPktSize:=stat.StdDev(pktSizes,nil)
	maxIdt,minIdt,meanIdt:=processStats(idts)
	stdvIdt:=stat.StdDev(idts,nil)

	//construct map
	report:=make(map[string]interface{})
	report["specifier"]=specifier
	report["stats"]=[]float64{
		minPktSize,
		maxPktSize,
		meanPktSize,
		stdvPktSize,
		minIdt,
		maxIdt,
		meanIdt,
		stdvIdt,
	}
	err:=SendMap(ip,port, report)
	if err!=nil{
		log.Fatalln(err)
	}

}

func randomFlowIdToPort(flowId int) (sport,dport int){
	sport=rand.Intn(65536-1500)+1500
	dport=rand.Intn(65536-1500)+1500
	return sport,dport
}

func (g *Generator)Start() (err error) {
	if g.Delay{
		time.Sleep(time.Millisecond*time.Duration(rand.Intn(10000)))
	}
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
	log.Printf("#Destination host %d, first %s,last %s",len(DstIPs),DstIPs[0],DstIPs[len(DstIPs)-1])
	log.Printf("#Destination host mac %d, first %s,last %s",len(DstMACs),DstMACs[0],DstMACs[len(DstMACs)-1])

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
	if pktFileCount==0{
		log.Fatalf("there is no pkt file in %s",g.PktsDir)
	}
	log.Printf("#pkt files %d\n",pktFileCount)
	//shuffle
	rand.Shuffle(len(pktFns), func(i, j int) {
		pktFns[i],pktFns[j]=pktFns[j],pktFns[i]
	})

	pktFileIdx:=0

	for{
		g.reset()
		//#read pkt file
		pktFile:=path.Join(g.PktsDir,pktFns[pktFileIdx])
		lines,err:=ReadLines(pktFile)
		//log.Printf("#lines %d",len(lines))
		if err!=nil{
			log.Fatalf("Error reading pkt file %s\n",pktFile)
		}
		for _,line:=range lines{
			content:=strings.Split(line," ")
			if len(content)!=5{
				log.Fatalf("Invalid pkt file %s\n",pktFile)
			}
			toSleep,err:=strconv.ParseFloat(content[0],64)
			if toSleep<0 && int(toSleep)!=-1{
				log.Fatalln("Invalid sleep time")
			}
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
			tsDiffInFlow,err:=strconv.ParseFloat(content[4],64)
			if tsDiffInFlow<0 && int(tsDiffInFlow)!=-1{
				log.Fatalln("Invalid ts diff in flow")
			}
			if err!=nil{
				log.Printf("Invalid ts diff in flow in pkt file %s\n\n", pktFile)
				break
			}
			dstIPStr:=DstIPs[flowId%nDsts]
			dstIP:=net.ParseIP(dstIPStr)
			dstMAC,_:=net.ParseMAC(DstMACs[flowId%nDsts])

			//determine sport and dport
			srcPort:=-1
			dstPort:=-1
			if ports,exsits:=g.flowId2Port[flowId];exsits{
				srcPort=ports[0]
				dstPort=ports[1]
			}else{
				srcPort,dstPort=randomFlowIdToPort(flowId)
				g.flowId2Port[flowId]=[2]int{srcPort,dstPort}
			}




			ether.DstMAC=dstMAC
			ipv4.DstIP=dstIP

			if proto=="TCP"{
				tcp.SrcPort= layers.TCPPort(srcPort)
				tcp.DstPort= layers.TCPPort(dstPort)
				ipv4.Protocol=6
				err=g.send(size,ether,ipv4,tcp,nil,true)
				if err!=nil{
					log.Fatal(err)
				}
			}else{
				udp.SrcPort= layers.UDPPort(srcPort)
				udp.DstPort= layers.UDPPort(dstPort)
				ipv4.Protocol=17
				err=g.send(size,ether,ipv4,nil,udp,false)
				if err!=nil{
					log.Fatal(err)
				}
			}
			_, exits := g.flowStats[flowId]
			if !exits {
				g.flowStats[flowId] = map[string][]float64{
					"pkt_size": make([]float64, 0),
					"idt":      make([]float64, 0),
				}
			}

			if g.Report {
				//collects
				if !g.sentRecord.Contains(flowId) {
					//log.Printf("hello : %d\n",len(g.flowStats[flowId]["pkt_size"]))
					//collect stats
					if len(g.flowStats[flowId]["pkt_size"]) == g.WinSize {
						//ok
						g.sentRecord.Add(flowId)
						specifier := [5]string{
							fmt.Sprintf("%d", srcPort),
							fmt.Sprintf("%d", dstPort),
							ipStr,
							dstIPStr,
							proto,
						}
						stats := g.flowStats[flowId]
						go processFlowStats(g.ControllerIP, g.ControllerPort, specifier, CopyMap(stats))
						delete(g.flowStats, flowId)
						g.sentRecord.Add(flowId)
					} else {
						g.flowStats[flowId]["pkt_size"] = append(g.flowStats[flowId]["pkt_size"], float64(size))
						g.flowStats[flowId]["idt"] = append(g.flowStats[flowId]["idt"], tsDiffInFlow)
					}
				}
			}

			if toSleep > 0 && g.Sleep {
				nano := int(1e9 * toSleep)
				time.Sleep(time.Duration(nano) * time.Nanosecond)
			}
		}

		pktFileIdx=(pktFileIdx+1)%pktFileCount
	}

}

//udp fragmentation
func (g *Generator) send(payloadSize int,ether *layers.Ethernet,ip *layers.IPv4,tcp *layers.TCP,udp *layers.UDP,isTCP bool) (err error){
	payloadPerPacketSize:=g.MTU-g.EmptySize
	count:=payloadSize/payloadPerPacketSize

	buffer:=g.buffer
	for ;count>0;count--{
		_ = buffer.Clear()
		payLoadPerPacket:=g.rawData[:payloadPerPacketSize]
		payloadSize-=payloadPerPacketSize
		if isTCP{
			err=gopacket.SerializeLayers(buffer,g.options,ether,ip,tcp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return err
			}
			err=g.handle.WritePacketData(buffer.Bytes())
			if err!=nil{
				return err
			}
		}else{
			err=gopacket.SerializeLayers(buffer,g.options,ether,ip,udp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return err
			}
			err=g.handle.WritePacketData(buffer.Bytes())
			if err!=nil{
				return err
			}
		}
	}

	_=buffer.Clear()
	if isTCP{
		err=gopacket.SerializeLayers(buffer,g.options,ether,ip,tcp,gopacket.Payload(g.rawData[:payloadSize]))
		if err!=nil{
			return err
		}
		err=g.handle.WritePacketData(buffer.Bytes())
		if err!=nil{
			return err
		}
	}else{
		err=gopacket.SerializeLayers(buffer,g.options,ether,ip,udp,gopacket.Payload(g.rawData[:payloadSize]))
		if err!=nil{
			return err
		}
		err=g.handle.WritePacketData(buffer.Bytes())
		if err!=nil{
			return err
		}

	}

	return nil
}

func (g *Generator)Init()  {
	g.flowStats=make(map[int]map[string][]float64)
	g.sentRecord=&IntSet{}
	g.buffer=gopacket.NewSerializeBuffer()
	g.flowId2Port=make(map[int][2]int)
	rand.Seed(time.Now().UnixNano())

}

func (g *Generator)reset(){
	g.sentRecord=&IntSet{}
	g.flowStats=make(map[int]map[string][]float64)
	g.sentRecord.init()
	_=g.buffer.Clear()
	g.flowId2Port=make(map[int][2]int)
}

