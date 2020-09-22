package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
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
	"os"
	"os/signal"
	"path"
	"strconv"
	"strings"
	"syscall"
	"time"
)

//type Specifier [5]string
//type Seq int64


type Generator struct {
	ID             int
	MTU            int
	EmptySize      int
	SelfID         int
	DestinationIDs []int
	PktsDir        string
	Int            string
	WinSize        int
	ControllerIP   string
	ControllerPort int
	Sleep          bool
	Report         bool
	Delay          bool
	DelayTime      int
	Debug          bool
	FlowType       int
	//whether enable force target
	ForceTarget bool
	Target      int

	ipStr  string
	macStr string

	rawData []byte
	handle  *pcap.Handle
	timeout time.Duration

	//flow-id ---> {pkt_size:[],idt:[]}
	statsToReport map[int]map[string][]float64
	sentRecord    *utils.IntSet
	buffer        gopacket.SerializeBuffer

	enablePktLossStats bool
	pktLossDir string


	//flowId2Port   map[int][2]int
	stopChannel chan struct{}

	flowIDToFiveTuple map[int][5]string
	flowIDToFlowDesc  map[int]*common.FlowDesc
	writerChan        chan *common.FlowDesc
	writer            *pktlosswriter

	flowIdToSeq map[int]int64
	periodPktCount map[int]int64

}

func processStats(nums []float64) (min, max, mean float64) {
	min = math.MaxFloat64
	max = -1
	validCount := 0
	sum := float64(0)
	for _, v := range nums {
		if v <= 0 {
			continue
		}
		validCount++
		sum += v
		if v > max {
			max = v
		}
		if v < min {
			min = v
		}
	}
	return min, max, sum / float64(validCount)
}

func processFlowStats(ip string, port int, specifier [5]string, stats map[string][]float64) {
	pktSizes := stats["pkt_size"]
	idts := stats["idt"]
	idts = utils.FilterFloat(idts, func(f float64) bool {
		return f > 0
	})
	if len(idts) == 0 {
		return
	}

	pktSizes = utils.FilterFloat(pktSizes, func(f float64) bool {
		return f >= 0
	})
	if len(pktSizes) == 0 {
		return
	}

	minPktSize, maxPktSize, meanPktSize := processStats(pktSizes)
	stdvPktSize := stat.StdDev(pktSizes, nil)
	maxIdt, minIdt, meanIdt := processStats(idts)
	stdvIdt := stat.StdDev(idts, nil)

	//construct map
	report := make(map[string]interface{})
	report["specifier"] = specifier
	report["stats"] = []float64{
		minPktSize,
		maxPktSize,
		meanPktSize,
		stdvPktSize,
		minIdt,
		maxIdt,
		meanIdt,
		stdvIdt,
	}
	err := utils.SendMap(ip, port, report)
	if err != nil {
		log.Println(err)
	}
}

func randomFlowIdToPort(flowId int) (sport, dport int) {
	sport = rand.Intn(65536-1500) + 1500
	dport = rand.Intn(65536-1500) + 1500
	return sport, dport
}

func (g *Generator) flushPktLossStats() {
	for _, fDesc := range g.flowIDToFlowDesc {
		g.writerChan <- fDesc
	}
}

func (g *Generator) Start() (err error) {

	log.Printf("DemoStart to generate")
	nDsts := len(g.DestinationIDs)
	log.Printf("# dsts %d\n", nDsts)
	utils.ShuffleInts(g.DestinationIDs)
	//init handler
	handle, err := pcap.OpenLive(g.Int, 1024, false, g.timeout)
	if err != nil {
		log.Fatalf("Cannot open device %s\n", g.Int)
	}
	defer handle.Close()
	g.handle = handle
	g.rawData = make([]byte, 1600)

	//self ip and mac
	g.ipStr, err = utils.GenerateIP(g.ID)
	if err != nil {
		log.Fatalf("Invalid generator id %d\n", g.ID)
	}

	ip := net.ParseIP(g.ipStr)
	ipv4.SrcIP = ip

	g.macStr, err = utils.GenerateMAC(g.ID)
	mac, _ := net.ParseMAC(g.macStr)
	ether.SrcMAC = mac

	if err != nil {
		log.Fatalf("Invalid generator id %d\n", g.ID)
	}

	DstIPs := make([]string, 0)
	DstMACs := make([]string, 0)
	for _, dstId := range g.DestinationIDs {
		ip, err := utils.GenerateIP(dstId)
		if err != nil {
			log.Fatalf("Generator: %d Error when generate ip for %d", g.ID, dstId)
		}
		DstIPs = append(DstIPs, ip)
		mac, err := utils.GenerateMAC(dstId)
		if err != nil {
			log.Fatalf("Generator: %d Error when generate mac for %d", g.ID, dstId)
		}
		DstMACs = append(DstMACs, mac)
	}
	log.Println(DstMACs)
	log.Printf("#Destination host %d, first %s,last %s", len(DstIPs), DstIPs[0], DstIPs[len(DstIPs)-1])
	log.Printf("#Destination host mac %d, first %s,last %s", len(DstMACs), DstMACs[0], DstMACs[len(DstMACs)-1])

	//count files
	pktFileCount := 0
	files, err := ioutil.ReadDir(g.PktsDir)
	pktFns := make([]string, 0)
	if err != nil {
		return err
	}
	for _, f := range files {
		if strings.Contains(f.Name(), "pkts") {
			pktFileCount++
			pktFns = append(pktFns, f.Name())
		}
	}
	if pktFileCount == 0 {
		log.Fatalf("there is no pkt file in %s", g.PktsDir)
	}
	log.Printf("#pkt files %d\n", pktFileCount)

	utils.ShuffleStrings(pktFns)

	pktFileIdx := 0
	log.Println("DemoStart to sleep for random time")
	if g.Delay {
		time.Sleep(time.Millisecond * time.Duration(rand.Intn(1000)))
	}
	log.Println("Sleep over.DemoStart injection")

	stopped := false
	for {
		//刷新packet loss stats到channel
		//正常情况下应该no work to do
		if g.enablePktLossStats {
			g.flushPktLossStats()
		}
		if stopped {
			if g.enablePktLossStats{
				close(g.writerChan)
			}
			break
		}
		rand.Shuffle(len(DstIPs), func(i, j int) {
			DstIPs[i], DstIPs[j] = DstIPs[j], DstIPs[i]
			DstMACs[i], DstMACs[j] = DstMACs[j], DstMACs[i]
		})

		g.reset()
		pktFile := path.Join(g.PktsDir, pktFns[pktFileIdx])
		lines, err := utils.ReadLines(pktFile)
		if err != nil {
			log.Fatalf("Error reading pkt file %s\n", pktFile)
		}

		log.Printf("pkt file %s: #lines: %d", pktFns[pktFileIdx], len(lines))

		for _, line := range lines {
			if stopped{
				break
			}
			select {
			case <-g.stopChannel:
				//break loop
				log.Println("Generator stop requested")
				stopped = true
				g.flushPktLossStats()
				g.flowIDToFlowDesc=make(map[int]*common.FlowDesc)
				break
			default:
				{
					content := strings.Split(line, " ")
					if len(content) != 6 {
						log.Fatalf("Invalid pkt file %s\n", pktFile)
					}
					toSleep, err := strconv.ParseFloat(content[0], 64)
					if toSleep < 0 && int(toSleep) != -1 {
						log.Fatalf("Invalid sleep time in pkt file %s\n", pktFile)
					}
					if err != nil {
						log.Fatalf("Invalid idt time in pkt file %s\n", pktFile)
					}
					size, err := strconv.Atoi(content[1])
					if err != nil {
						log.Fatalf("Invalid pkt size in pkt file %s\n", pktFile)
					}
					proto := content[2]
					flowId, err := strconv.Atoi(content[3])
					if err != nil {
						log.Fatalf("Invalid flow id in pkt file %s\n", pktFile)
					}

					tsDiffInFlow, err := strconv.ParseFloat(content[4], 64)
					if tsDiffInFlow < 0 && int(tsDiffInFlow) != -1 {
						log.Fatalln("Invalid ts diff in flow")
					}
					if err != nil {
						log.Fatalf("Invalid ts diff in flow in pkt file %s\n", pktFile)
					}
					last, err := strconv.ParseInt(content[5], 10, 64)
					if err != nil {
						log.Fatalf("Invalid last payload indicator in pkt file %s\n", pktFile)
					}
					isLastL4Payload := false
					if last > 0 {
						log.Printf("Flow %d finished\n", flowId)
						isLastL4Payload = true
					}

					if _, exists := g.flowIDToFiveTuple[flowId]; !exists {
						//map and save
						sp, dp := randomFlowIdToPort(flowId)
						var dip string
						if g.ForceTarget {
							dip, err = utils.GenerateIP(g.Target)
							if err != nil {
								log.Fatalf("Cannot generate ip for given id:%d\n", g.Target)
							}
							//log.Printf("Force target ip:%s\n", dip)
						} else {
							dip = DstIPs[flowId%nDsts]
						}
						g.flowIDToFiveTuple[flowId] = [5]string{
							g.ipStr,
							strconv.Itoa(sp),
							dip,
							strconv.Itoa(dp),
							proto,
						}
					}

					//sip,sport,dip,dport,proto
					fiveTuple := g.flowIDToFiveTuple[flowId]
					srcPort, err := strconv.Atoi(fiveTuple[1])
					if err != nil {
						log.Fatalf("Error when parsing src port,five tuple:%s", fiveTuple)
					}

					dstIPStr := fiveTuple[2]
					dstIP := net.ParseIP(dstIPStr)
					ipv4.DstIP = dstIP

					var dstMACStr string
					if g.ForceTarget {
						dstMACStr, err = utils.GenerateMAC(g.Target)
						if err != nil {
							log.Fatalf("Cannot generate mac for given id:%d\n", g.Target)
						}
					} else {
						dstMACStr = DstMACs[flowId%nDsts]
					}
					ether.DstMAC, _ = net.ParseMAC(dstMACStr)

					dstPort, err := strconv.Atoi(fiveTuple[3])
					if err != nil {
						log.Fatalf("Error when parsing dst port,five tuple:%s", fiveTuple)
					}

					if proto == "TCP" {
						tcp.SrcPort = layers.TCPPort(srcPort)
						tcp.DstPort = layers.TCPPort(dstPort)
						ipv4.Protocol = 6

						if g.enablePktLossStats{
							updatedPeriodPktCount,updatedSeqNum,err:=sendWithSeq(
								handle,
								g.buffer,
								g.rawData,
								size,
								g.MTU-g.EmptySize,
								ether,
								vlan,
								ipv4,
								tcp,
								udp,
								true,
								true,
								isLastL4Payload,
								g.flowIdToSeq[flowId],
								g.periodPktCount[flowId],
								)
							if err != nil {
								log.Fatal(err)
							}
							g.periodPktCount[flowId]=updatedPeriodPktCount%100
							g.flowIdToSeq[flowId]=updatedSeqNum
						}else{
							err = send(g.handle, g.buffer, g.rawData, size, g.MTU-g.EmptySize, ether, vlan, ipv4, tcp, udp, true, true, isLastL4Payload)
							if err != nil {
								log.Fatal(err)
							}
						}

					} else {
						udp.SrcPort = layers.UDPPort(srcPort)
						udp.DstPort = layers.UDPPort(dstPort)
						ipv4.Protocol = 17
						//err = send(g.handle, g.buffer, g.rawData, size, g.MTU-g.EmptySize, ether, vlan, ipv4, tcp, udp, false, true, isLastL4Payload)
						//if err != nil {
						//	log.Fatal(err)
						//}

						if g.enablePktLossStats{
							updatedPeriodPktCount,updatedSeqNum,err:=sendWithSeq(
								handle,
								g.buffer,
								g.rawData,
								size,
								g.MTU-g.EmptySize,
								ether,
								vlan,
								ipv4,
								tcp,
								udp,
								true,
								true,
								isLastL4Payload,
								g.flowIdToSeq[flowId],
								g.periodPktCount[flowId],
							)
							if err != nil {
								log.Fatal(err)
							}
							g.periodPktCount[flowId]=updatedPeriodPktCount%100
							g.flowIdToSeq[flowId]=updatedSeqNum
						}else{
							err = send(g.handle, g.buffer, g.rawData, size, g.MTU-g.EmptySize, ether, vlan, ipv4, tcp, udp, true, true, isLastL4Payload)
							if err != nil {
								log.Fatal(err)
							}
						}
					}

					//report
					_, exits := g.statsToReport[flowId]
					if !exits {
						g.statsToReport[flowId] = map[string][]float64{
							"pkt_size": make([]float64, 0),
							"idt":      make([]float64, 0),
						}
					}

					if g.Report {
						//collects
						if !g.sentRecord.Contains(flowId) {
							//log.Printf("hello : %d\n",len(g.statsToReport[flowId]["pkt_size"]))
							//collect stats
							if len(g.statsToReport[flowId]["pkt_size"]) == g.WinSize {
								//ok
								specifier := [5]string{
									fmt.Sprintf("%d", srcPort),
									fmt.Sprintf("%d", dstPort),
									g.ipStr,
									dstIPStr,
									proto,
								}
								stats := g.statsToReport[flowId]
								go processFlowStats(g.ControllerIP, g.ControllerPort, specifier, utils.CopyMap(stats))
								delete(g.statsToReport, flowId)
								g.sentRecord.Add(flowId)
							} else {
								g.statsToReport[flowId]["pkt_size"] = append(g.statsToReport[flowId]["pkt_size"], float64(size))
								g.statsToReport[flowId]["idt"] = append(g.statsToReport[flowId]["idt"], tsDiffInFlow)
							}
						}
					}

					if g.enablePktLossStats {
						if _, exists := g.flowIDToFlowDesc[flowId]; !exists {
							fd := &common.FlowDesc{
								SrcIP:           g.ipStr,
								SrcPort:         srcPort,
								DstIP:           dstIPStr,
								DstPort:         dstPort,
								Proto:           proto,
								TxStartTs:       utils.NowInMilli(),
								TxEndTs:         0,
								FlowType:        fType,
								ReceivedPackets: 0,
								MinDelay:        0,
								MaxDelay:        0,
								MeanDelay:       0,
								StdVarDelay:     0,
							}
							g.flowIDToFlowDesc[flowId] = fd
						}

						fDesc := g.flowIDToFlowDesc[flowId]
						fDesc.ReceivedPackets += 1

						if isLastL4Payload {
							fDesc.TxEndTs = utils.NowInMilli()
							//send
							g.writerChan <- fDesc
							//delete
							delete(g.flowIDToFlowDesc, flowId)
						}
					}

					if toSleep > 0 && g.Sleep {
						nano := int(toSleep)
						time.Sleep(time.Duration(nano) * time.Nanosecond)
					}
				}
			}
		}

		pktFileIdx = (pktFileIdx + 1) % pktFileCount
	}
	return nil
}

func (g *Generator) Init() {
	vlan = &layers.Dot1Q{
		VLANIdentifier: 3,
		Type:           layers.EthernetTypeIPv4,
	}
	ether = &layers.Ethernet{
		EthernetType: layers.EthernetTypeDot1Q,
	}
	ipv4 = &layers.IPv4{
		Version:    4,   //uint8
		IHL:        5,   //uint8
		TOS:        0,   //uint8
		Id:         0,   //uint16
		Flags:      0,   //IPv4Flag
		FragOffset: 0,   //uint16
		TTL:        255, //uint8
	}
	tcp = &layers.TCP{}
	udp = &layers.UDP{}

	rand.Seed(time.Now().UnixNano())

	options.FixLengths = true
	payloadPerPacketSize = g.MTU - g.EmptySize
	g.statsToReport = make(map[int]map[string][]float64)
	g.sentRecord = &utils.IntSet{}
	g.buffer = gopacket.NewSerializeBuffer()
	//g.flowId2Port=make(map[int][2]int)
	g.stopChannel = make(chan struct{})
	g.flowIDToFiveTuple = make(map[int][5]string)
	g.flowIDToFlowDesc=make(map[int]*common.FlowDesc)

	//register signal
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)
	go func() {
		sig := <-sigs
		log.Printf("Generator received signal %s\n", sig)
		log.Println("DemoStart to shutdown sender")
		g.stopChannel <- struct{}{}
	}()

	if g.enablePktLossStats {

		g.writerChan = make(chan *common.FlowDesc, 10240)
		g.writer = NewPktLossWriter(1024, g.pktLossDir, g.writerChan)
		//start writer
		go func() {
			g.writer.start()
		}()
	}
	g.flowIdToSeq=make(map[int]int64)
	g.periodPktCount=make(map[int]int64)
}

func (g *Generator) reset() {
	rand.Seed(time.Now().UnixNano())
	g.sentRecord = &utils.IntSet{}
	g.sentRecord.Init()

	g.statsToReport = make(map[int]map[string][]float64)

	g.flowIDToFiveTuple = make(map[int][5]string)

	g.flowIdToSeq=make(map[int]int64)
	g.periodPktCount=make(map[int]int64)

}
