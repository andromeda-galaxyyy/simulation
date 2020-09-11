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
	"time"
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

	tickerToWorkerSigChan chan common.Signal
	workerToWriterSigChan chan common.Signal
	sigChan chan common.Signal

	//是否启动定时刷新
	enablePeriodFlush bool
	//刷新间隔
	flushInterval int64

}

func (w *worker) Init(){
	w.fiveTupleToFDesc=make(map[[5]string]*common.FlowDesc)
	w.writerChannel=make(chan *common.FlowDesc,102400)
	w.flowWriter=NewDefaultWriter(w.id, w.writerChannel)
	w.sigChan=make(chan common.Signal,10)

	w.tickerToWorkerSigChan =make(chan common.Signal,10)
	w.workerToWriterSigChan =make(chan common.Signal,10)
	w.flowWriter.sigChan =w.workerToWriterSigChan

	w.flowDelay=make(map[[5]string][]int64)
	w.flowDelayFinished=utils.NewSpecifierSet()

}

func (w *worker) processPacket(packet *gopacket.Packet) {
	specifier := [5]string{}
	ipLayer := (*packet).Layer(layers.LayerTypeIPv4)
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

	flowFinished := utils.GetBit(l4Payload[8], 7) == 1

	// 获取流类型
	l4Payload[8] = utils.UnsetBit(l4Payload[8], 7)
	flowType := int(l4Payload[8])

	//记录流类型
	if _, exists := w.fiveTupleToFtype[specifier]; !exists {
		w.fiveTupleToFtype[specifier] = flowType
	}

	delay:=utils.BytesToInt64(l4Payload[:8])

	w.flowDelay[specifier] = append(w.flowDelay[specifier], delay)

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
		go w.processPktStats(desc,utils.CopyInt64Slice(w.flowDelay[specifier]))
		log.Println("flow finished")
		delete(w.flowDelay, specifier)
		delete(w.fiveTupleToFtype, specifier)
	}
}

func (w *worker) start(packetChannel chan gopacket.Packet, wg *sync.WaitGroup) {
	go w.flowWriter.Start()
	defer wg.Done()
	if w.enablePeriodFlush{
		log.Printf("Writer id: %d enable period flush, timeout:%d\n",w.id,w.flushInterval)
		stopped:=false
		// 每五分钟刷新一次
		ticker:=time.NewTicker(time.Duration(w.flushInterval)* time.Second)
		stop2tickerChan:=make(chan common.Signal,1)
		//启动定时器
		go func() {
			for{
				select {
				case <-ticker.C:
					w.tickerToWorkerSigChan <- common.FlushSignal
					continue

				case <-stop2tickerChan:
					ticker.Stop()
					return
				}
			}
		}()

		for{
			if stopped{
				break
			}
			select {
			case packet:=<-packetChannel:
				w.processPacket(&packet)
				continue
			case <-w.tickerToWorkerSigChan:
				//todo 刷新
				// 暂时停止收包，将所有的包打包送给writer
				log.Println("period flush")
				for specifier,delays:=range w.flowDelay{
					desc:=w.fiveTupleToFDesc[specifier]
					w.processPktStats(desc,delays)
				}

				//reset data structure
				w.flowDelay=make(map[[5]string][]int64)
				w.flowDelayFinished=utils.NewSpecifierSet()
				w.fiveTupleToFDesc=make(map[[5]string]*common.FlowDesc)
				w.workerToWriterSigChan<-common.FlushSignal
				continue
			case sig:=<-w.sigChan:
				if common.IsStopSignal(sig){
					log.Printf("Worker id: %d stop requested",w.id)
					//给ticker发送信号，停止计时
					log.Printf("Worker id %d sending signal to ticker",w.id)
					stop2tickerChan<- common.StopSignal
					stopped=true
					break
				}else if common.IsFlushSig(sig){
					log.Printf("Worker id:%d received flush signal from dispatcher,not implemented yet \n",w.id)

				}

			}
		}
	}else{
		for packet:=range packetChannel{
			w.processPacket(&packet)
		}
	}



	log.Printf("worker %d complete Flush cache...\n", w.id)
	w.completeFlush()
	//time.Sleep(10 * time.Second)
	log.Printf("Shutting down worker %d...Closing writer channel...\n", w.id)
	close(w.writerChannel)
	w.workerToWriterSigChan<-common.StopSignal
}

//程序截止的时候，停止完全flush
func (w *worker) completeFlush() {
	for specifier, delays := range w.flowDelay {
		desc:=w.fiveTupleToFDesc[specifier]
		w.processPktStats(desc,delays)
	}
}


func (w *worker) processPktStats(desc *common.FlowDesc,delays []int64) {
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

	desc.MinDelay=min
	desc.MaxDelay=max
	desc.StdVarDelay=std
	desc.MeanDelay=mean
	desc.RxEndTs=utils.NowInMilli()

	w.writerChannel <-desc
}
