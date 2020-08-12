package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"log"
	"math"
	"strconv"
	"sync"
)

type worker struct {
	id int
	//观测窗口大小
	delaySampleSize int
	//some private fields
	flowDelay         map[[5]string][]int64
	flowDelayFinished *utils.SpecifierSet
	flowWriter        *writer
	//flowType
	fiveTupleToFtype map[[5]string]int

	//writer channel
	writerChannel      chan *common.FlowDesc
	fiveTupleToFDesc map[[5]string]*common.FlowDesc
	enablePktLossStats bool
}

func (w *worker) Init(){
	w.fiveTupleToFDesc=make(map[[5]string]*common.FlowDesc)
	w.writerChannel=make(chan *common.FlowDesc,102400)
	w.flowWriter=NewDefaultWriter(w.id, w.writerChannel)
}

func (w *worker) processPacket(packet *gopacket.Packet) {
	specifier := [5]string{}
	ipLayer := (*packet).Layer(layers.LayerTypeIPv4)
	meta := (*packet).Metadata()
	captureInfo := meta.CaptureInfo
	captureTime := captureInfo.Timestamp.UnixNano() / 1e6
	if ipLayer == nil {
		return
	}

	ip, _ := ipLayer.(*layers.IPv4)
	sip := ip.SrcIP.String()
	dip := ip.DstIP.String()

	l4Payload := (*packet).TransportLayer().LayerPayload()
	tcpLayer := (*packet).Layer(layers.LayerTypeTCP)

	var sp,dp int

	if tcpLayer != nil {
		tcp, _ := tcpLayer.(*layers.TCP)
		sp=int(tcp.SrcPort)
		dp=int(tcp.DstPort)
		sport := strconv.Itoa(int(tcp.SrcPort))
		dport := strconv.Itoa(int(tcp.DstPort))
		specifier[0] = sip
		specifier[1] = sport
		specifier[2] = dip
		specifier[3] = dport
		specifier[4] = "TCP"
	} else {
		udpLayer := (*packet).Layer(layers.LayerTypeUDP)
		if udpLayer != nil {
			udp, _ := udpLayer.(*layers.UDP)
			sp=int(udp.SrcPort)
			dp=int(udp.DstPort)
			sport := strconv.Itoa(int(udp.SrcPort))
			dport := strconv.Itoa(int(udp.DstPort))
			specifier[0] = sip
			specifier[1] = sport
			specifier[2] = dip
			specifier[3] = dport
			specifier[4] = "UDP"
		}
	}
	if len(l4Payload) < 9 {
		return
	}

	//todo flowType
	flowFinished := utils.GetBit(l4Payload[8], 7) == 1

	// 获取流类型
	l4Payload[8] = utils.UnsetBit(l4Payload[8], 7)
	flowType := int(l4Payload[8])

	//记录流类型
	if _, exists := w.fiveTupleToFtype[specifier]; !exists {
		w.fiveTupleToFtype[specifier] = flowType
	}

	sendTime := utils.BytesToInt64(l4Payload[:8])

	if sendTime != 0 {
		w.flowDelay[specifier] = append(w.flowDelay[specifier], captureTime-sendTime)
	}

	if _,exists:= w.fiveTupleToFDesc[specifier];!exists{
		w.fiveTupleToFDesc[specifier]=&common.FlowDesc{
			SrcIP:       sip,
			SrcPort:     sp,
			DstIP:       dip,
			DstPort:     dp,
			Proto:       specifier[4],
			TxStartTs:   0,
			TxEndTs:     0,
			RxStartTs:   utils.NowInMilli(),
			RxEndTs:     0,
			FlowType:    flowType,
			Packets:     0,
			MinDelay:    0,
			MaxDelay:    0,
			MeanDelay:   0,
			StdVarDelay: 0,
		}
	}
	desc:= w.fiveTupleToFDesc[specifier]
	desc.Packets+=1


	if flowFinished {
		//must copied
		go w.processPktStats(specifier, utils.CopyInt64Slice(w.flowDelay[specifier]))
		log.Println("flow finished")
		delete(w.flowDelay, specifier)
		delete(w.fiveTupleToFtype, specifier)
	}
}

func (w *worker) start(packetChannel chan gopacket.Packet, wg *sync.WaitGroup) {
	go w.flowWriter.Start()
	defer wg.Done()
	for packet := range packetChannel {
		w.processPacket(&packet)
	}
	log.Printf("worker %d completeFlush cache...\n", w.id)
	w.completeFlush()
	//time.Sleep(10 * time.Second)
	log.Printf("Shutting down worker %d...Closing writer channel...\n", w.id)
	close(w.writerChannel)
}

//程序截止的时候，停止完全flush
func (w *worker) completeFlush() {
	for specifier, delays := range w.flowDelay {
		w.processPktStats(specifier, delays)
	}
}


func (w *worker) processPktStats(specifier [5]string, delays []int64) {
	//find min,max,average,stdvar
	min := int64(math.MaxInt64)
	max := int64(math.MinInt64)
	mean := 0.0
	std := 0.0
	l := len(delays)
	s := 0.0
	for _, v := range delays {
		if v > max {
			max = v
		}
		if v < min {
			min = v
		}
		mean += float64(v) / float64(l)
	}
	for _, v := range delays {
		d := float64(v)
		diff := d - mean
		s += diff * diff
	}
	s /= float64(l)
	std = math.Sqrt(s)

	if desc,exists:= w.fiveTupleToFDesc[specifier];!exists{
		return
	}else{
		desc.MinDelay=min
		desc.MaxDelay=max
		desc.StdVarDelay=std
		desc.MeanDelay=mean
		desc.RxEndTs=utils.NowInMilli()

		fType:=0
		if _, exists := w.fiveTupleToFtype[specifier]; exists {
			fType = w.fiveTupleToFtype[specifier]
		}
		desc.FlowType=fType
		w.writerChannel <-desc
	}

}
