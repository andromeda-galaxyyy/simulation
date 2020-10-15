package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"fmt"
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
	//some private fields
	flowDelay         map[[5]string][]int64
	flowWriter        *writer
	//flowType
	fTypeRecord    map[[5]string]int
	//pktCountRecord map[[5]string]int64
	seqRecord map[[5]string]int64

	//writer channel
	delayChannel       chan *common.FlowDesc
	lossChannel chan *common.FlowDesc

	//delay和loss是两个数据结构
	fiveTupleToFDescForDelay map[[5]string]*common.FlowDesc
	fiveTupleToFDescForLoss map[[5]string] *common.FlowDesc

	enablePktLossStats       bool

	tickerToWorkerSigChan chan common.Signal
	workerToWriterSigChan chan common.Signal
	sigChan chan common.Signal

	//是否启动定时刷新
	enablePeriodFlush bool
	//刷新间隔
	flushInterval int64
}



//关于定时刷新时钟的位置
// 应该可以放到writer，但是这里放到了worker处
// 考虑到writer的职责应该尽量单一，状态维护放到worker处
func (w *worker) Init(){
	w.fiveTupleToFDescForDelay =make(map[[5]string]*common.FlowDesc)
	w.fiveTupleToFDescForLoss=make(map[[5]string]*common.FlowDesc)
	w.delayChannel =make(chan *common.FlowDesc,102400)
	w.lossChannel=make(chan *common.FlowDesc,102400)

	w.flowWriter=NewDefaultWriter(w.id)

	w.flowWriter.lossChannel=w.lossChannel
	w.flowWriter.delayChannel=w.delayChannel
	//w.flowWriter.delayChannel=w.delayChannel
	w.sigChan=make(chan common.Signal,10)

	w.tickerToWorkerSigChan =make(chan common.Signal,10)
	w.workerToWriterSigChan =make(chan common.Signal,10)
	w.flowWriter.sigChan =w.workerToWriterSigChan

	w.flowDelay=make(map[[5]string][]int64)
	w.seqRecord=make(map[[5]string]int64)

}

func (w *worker) processPacket(packet *gopacket.Packet) {
	//todo check panic reason
	defer func() {
		if r:=recover();r!=nil{
			fmt.Println("Recover from panic")
		}
	}()
	if nil==packet{
		return
	}
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
	isSeqPkt:=false

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
		}else{
			return
		}
	}
	if len(l4Payload) <9 {
		return
	}

	isSeqPkt= utils.GetBit(l4Payload[8],2)==1
	l4Payload[8]=utils.UnsetBit(l4Payload[8],2)
	flowFinished := utils.GetBit(l4Payload[8], 7) == 1
	l4Payload[8] = utils.UnsetBit(l4Payload[8], 7)




	// 获取流类型
	flowType := int(l4Payload[8])
	if flowType>3{
		log.Fatalf("Invalid flow type %d\n", flowType)
	}

	//记录流类型
	if !isSeqPkt{
		if _, exists := w.fTypeRecord[specifier]; !exists {
			w.fTypeRecord[specifier] = flowType
		}
	}


	delayOrSeqNum :=utils.BytesToInt64(l4Payload[:8])

	if _,exists:= w.fiveTupleToFDescForDelay[specifier];!exists{
		w.fiveTupleToFDescForDelay[specifier]=&common.FlowDesc{
			SrcIP:           sip,
			SrcPort:         sp,
			DstIP:           dip,
			DstPort:         dp,
			Proto:           specifier[4],
			TxStartTs:       0,
			TxEndTs:         0,
			RxStartTs:       utils.NowInMilli(),
			RxEndTs:         0,
			FlowType:        flowType,
			ReceivedPackets: 0,
			MinDelay:        0,
			MaxDelay:        0,
			MeanDelay:       0,
			StdVarDelay:     0,
		}
	}

	if _,exits:=w.fiveTupleToFDescForLoss[specifier];!exits{
		w.fiveTupleToFDescForLoss[specifier]=&common.FlowDesc{
			SrcIP:           sip,
			SrcPort:         sp,
			DstIP:           dip,
			DstPort:         dp,
			Proto:           specifier[4],
			TxStartTs:       0,
			TxEndTs:         0,
			RxStartTs:       utils.NowInMilli(),
			RxEndTs:         0,
			FlowType:        flowType,
			ReceivedPackets: 0,
			Loss:            0,
			PeriodPackets:   0,
			PeriodLoss:      0,
			MinDelay:        0,
			MaxDelay:        0,
			MeanDelay:       0,
			StdVarDelay:     0,
		}
	}



	lossDesc:=w.fiveTupleToFDescForLoss[specifier]
	delayDesc := w.fiveTupleToFDescForDelay[specifier]

	if isSeqPkt{
		//log.Printf("Specifier %s,packet len %d\n",specifier,len(l4Payload))
		seq:=delayOrSeqNum
		if w.seqRecord[specifier]==seq{
			log.Printf("Worker %d:possible duplicate seq number %d\b",w.id,seq)
		}
		if w.seqRecord[specifier]>seq{
			log.Printf("Worker %d:invalid seq number %d>%d\n",w.id,w.seqRecord[specifier],seq)
		}
		periodLoss,_:=computeLoss(lossDesc,w.seqRecord[specifier],seq)
		w.seqRecord[specifier]=seq
		lossDesc.PeriodLoss=periodLoss
		w.lossChannel<- lossDesc
		delete(w.fiveTupleToFDescForLoss,specifier)
	}else{
		delay:=delayOrSeqNum
		w.flowDelay[specifier] = append(w.flowDelay[specifier], delay)
		delayDesc.ReceivedPackets +=1
		lossDesc.PeriodPackets+=1
		lossDesc.ReceivedPackets+=1
	}



	if flowFinished {
		//must copied
		go w.processPktStats(delayDesc,utils.CopyInt64Slice(w.flowDelay[specifier]))
		//log.Println("flow finished")
		delete(w.flowDelay, specifier)
		delete(w.fTypeRecord, specifier)
		delete(w.seqRecord,specifier)
		delete(w.fiveTupleToFDescForLoss,specifier)
		delete(w.fiveTupleToFDescForDelay,specifier)
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
				// loss 统计无法跟时钟同步，但是writer的刷新行为可以跟时钟同步
				//log.Printf("Worker %d period flush",w.id)

				for specifier,delays:=range w.flowDelay{
					desc:=w.fiveTupleToFDescForDelay[specifier]
					w.processPktStats(desc,delays)
				}

				//reset data structure
				w.flowDelay=make(map[[5]string][]int64)
				w.fiveTupleToFDescForDelay =make(map[[5]string]*common.FlowDesc)
				w.workerToWriterSigChan<-common.FlushSignal
				continue
			case sig:=<-w.sigChan:
				if common.IsStopSignal(sig){
					//log.Printf("Worker id: %d stop requested",w.id)
					//给ticker发送信号，停止计时
					//log.Printf("Worker id %d sending signal to ticker",w.id)
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


	log.Printf("worker %d complete FlushDelayStats delayCache...\n", w.id)
	w.completeFlush()
	//time.Sleep(10 * time.Second)
	log.Printf("Shutting down worker %d...Closing writer channel...\n", w.id)
	close(w.delayChannel)
	w.workerToWriterSigChan<-common.StopSignal
}

//程序截止的时候，停止完全flush
//丢包率无法刷新到writer处
func (w *worker) completeFlush() {
	for specifier, delays := range w.flowDelay {
		desc:=w.fiveTupleToFDescForDelay[specifier]
		w.processPktStats(desc,delays)
	}
}


/**
 返回某时间段的丢包率
only implement period loss now
收包数量估计算法,避免两个影响因素
1.中间有seq包丢失
2.包乱序

当出现一种情况时：
如果1 seq包丢失但不乱序,那么可以根据lastSeq和currSeq估计出来，
如果2 Seq包乱序，Seq先于数据包出现，那么可以根据已经统计的包的数量通过roundup估计出来
如果更复杂的情况出现，无法估计
 */
func computeLoss(desc *common.FlowDesc, lastSeqNum int64,currSeqNum int64)(float64,error){
	estimated1 :=100*(currSeqNum-lastSeqNum)

	return 1-float64(desc.PeriodPackets)/float64(estimated1),nil
}





func (w *worker) processPktStats(desc *common.FlowDesc,delays []int64) {
	//find min,max,average,stdvar
	min := int64(math.MaxInt64)
	max := int64(math.MinInt64)
	mean := 0.0
	std := 0.0
	s := 0.0
	count:=0

	for _, v := range delays {
		if v<=0{
			continue
		}
		count+=1
		if v > max {
			max = v
		}
		if v < min {
			min = v
		}
		mean += float64(v)
	}
	if count==0{
		return
	}

	mean/=float64(count)
	for _, v := range delays {
		if v<=0{
			continue
		}
		d := float64(v)
		diff := d - mean
		s += diff * diff
	}

	s /= float64(count)
	std = math.Sqrt(s)


	desc.MinDelay=min
	desc.MaxDelay=max
	desc.StdVarDelay=std
	desc.MeanDelay=mean
	desc.RxEndTs=utils.NowInMilli()

	w.delayChannel <-desc
}
