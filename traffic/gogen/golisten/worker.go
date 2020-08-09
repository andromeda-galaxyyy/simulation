package main

import (
	"chandler.com/gogen/utils"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"log"
	"math"
	"strconv"
	"sync"
	"time"
)

type worker struct {
	id int
	//观测窗口大小
	delaySampleSize int
	//some private fields
	flowDelay map[[5]string] []int64
	flowDelayFinished *utils.SpecifierSet
	flowWriter *writer
	//flowType
	flowTypes map[[5]string] int

	//writer channel
	writerChannel chan *flowDesc
}


func (worker *worker)processPacket(packet *gopacket.Packet)  {
	//sport,dport,sip,dip,proto
	specifier:=[5]string{}
	ipLayer:=(*packet).Layer(layers.LayerTypeIPv4)
	meta:=(*packet).Metadata()
	captureInfo:=meta.CaptureInfo
	captureTime:=captureInfo.Timestamp.UnixNano()/1e6
	if ipLayer ==nil{
		return
	}

	ip,_:=ipLayer.(*layers.IPv4)
	sip=ip.SrcIP.String()
	dip=ip.DstIP.String()

	l4Payload:=(*packet).TransportLayer().LayerPayload()
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
	}else{
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
		}
	}
	if len(l4Payload)<9{
		return
	}

	//todo flowType
	flowFinished:= utils.GetBit(l4Payload[8],7)==1

	// 获取流类型
	l4Payload[8]=utils.UnsetBit(l4Payload[8],7)
	flowType:=int(l4Payload[8])

	//记录流类型
	if _,exists:=worker.flowTypes[specifier];!exists{
		worker.flowTypes[specifier]=flowType
	}

	sendTime:=utils.BytesToInt64(l4Payload[:8])

	if sendTime!=0{
		worker.flowDelay[specifier]=append(worker.flowDelay[specifier],captureTime-sendTime)
	}

	if flowFinished {
		//must copied
		go worker.processPktDelays(specifier,utils.CopyInt64Slice(worker.flowDelay[specifier]),flowType)
		log.Println("flow finished")
		delete(worker.flowDelay,specifier)
		delete(worker.flowTypes,specifier)
	}
}

func (w *worker)start(packetChannel chan gopacket.Packet,wg *sync.WaitGroup)  {
	go w.flowWriter.Start()
	defer wg.Done()
	for packet:=range packetChannel{
		w.processPacket(&packet)
	}
	log.Printf("worker %d completeFlush cache...\n",w.id)
	w.completeFlush()
	time.Sleep(10*time.Second)
	log.Printf("Shutting down worker %d...Closing writer channel...\n",w.id)
	close(w.writerChannel)
}

//程序截止的时候，停止完全flush
func (w *worker) completeFlush()  {
	fType:=0
	for specifier,delays:=range w.flowDelay{
		if _,exists:=w.flowTypes[specifier];exists{
			fType=w.flowTypes[specifier]
		}
		w.processPktDelays(specifier,delays,fType)
	}
}

//计算密集型
//可能会阻塞 但是没关系，概率很小
//sport dport sip dip proto
func (w *worker)processPktDelays(specifier [5]string,delays []int64,flowType int){
	//find min,max,average,stdvar
	min:=int64(math.MaxInt64)
	max:=int64(math.MinInt64)
	mean:=0.0
	std:=0.0
	l:=len(delays)
	s:=0.0
	for _,v:=range delays{
		if v>max{
			max=v
		}
		if v<min{
			min=v
		}
		mean+= float64(v)/float64(l)
	}
	for _,v:=range delays{
		d:=float64(v)
		diff:=d-mean
		s+= diff*diff
	}
	s/=float64(l)
	std=math.Sqrt(s)
	fs:=&flowDesc{
		sport:       specifier[0],
		dport:       specifier[1],
		sip:         specifier[2],
		dip:         specifier[3],
		proto:       specifier[4],
		minDelay:    min,
		maxDelay:    max,
		meanDelay:   mean,
		stdvarDelay: std,
		flowType:    flowType,
	}
	//todo possible panic
	w.writerChannel<-fs
}