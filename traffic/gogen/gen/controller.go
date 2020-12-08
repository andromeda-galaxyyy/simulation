package main

import (
	"chandler.com/gogen/utils"
	"io/ioutil"
	"log"
	"math/rand"
	"os"
	"os/signal"
	"path"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"chandler.com/gogen/common"
	"github.com/google/gopacket"
)

type controller struct {
	id          int
	flowCounter uint64

	waiter      *sync.WaitGroup
	numWorkers int
	workers     []*generator
	specifiedPktFn string
	mtu                int
	emptySize          int
	selfID             int64
	destinationIDs     []int
	pktsDir            string
	intf               string
	winSize            int
	controllerIP       string
	controllerPort     int
	sleep              bool
	report             bool
	delay              bool
	delayDuration      int
	debug              bool
	forceTarget        bool
	target             int
	enablePktLossStats bool
	pktLossDir         string
	flowType           int

	counterWriter *common.FCounterWriter

	rip   string
	rport int

}

func (c *controller) Init() error {
	c.waiter = &sync.WaitGroup{}
	c.waiter.Add(c.numWorkers)
	c.workers = make([]*generator, 0)

	//random readlines
	var pktFileCount int

	files, err := ioutil.ReadDir(c.pktsDir)
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
		log.Fatalf("there is no pkt file in %s", c.pktsDir)
	}
	var pktFile string
	if len(c.specifiedPktFn)==0{
		pktFile=path.Join(c.pktsDir,pktFns[rand.Intn(pktFileCount)])
	}else{
		pktFile=c.specifiedPktFn
	}
	lines,err:=utils.ReadLines(pktFile)

	if err!=nil{
		log.Fatalf("Error reading pkt file %s\n", pktFile)
	}

	for i := 0; i < c.numWorkers; i++ {
		if len(c.specifiedPktFn)!=0{
			log.Printf("Specified a pkts file %s\n",c.specifiedPktFn)
		}
		c.workers = append(c.workers, &generator{
			ID:                 c.id,
			MTU:                c.mtu,
			EmptySize:          c.emptySize,
			SelfID:             i,
			DestinationIDs:     c.destinationIDs,
			PktsDir:            c.pktsDir,
			Int:                c.intf,
			WinSize:            c.winSize,
			ControllerIP:       c.controllerIP,
			ControllerPort:     c.controllerPort,
			Sleep:              c.sleep,
			Report:             c.report,
			Delay:              c.delay,
			DelayTime:          c.delayDuration,
			Debug:              c.debug,
			FlowType:           0,
			ForceTarget:        c.forceTarget,
			Target:             c.target,
			enablePktLossStats: c.enablePktLossStats,
			pktLossDir:         c.pktLossDir,
			waiter:             c.waiter,
			options:            gopacket.SerializeOptions{},
			fType:              c.flowType,
			specifiedPktFn: c.specifiedPktFn,
			selfLoadPkt: false,
			lines: lines,
		})
	}

	for _,g:=range c.workers{
		g.Init()
	}

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)
	stopTickerChan := make(chan common.Signal, 1)
	go func() {
		sig := <-sigs
		log.Printf("generator received signal %s\n", sig)
		stopTickerChan <- common.StopSignal
		for _,g:=range c.workers{
			g.stopChannel<-struct{}{}
		}
	}()

	c.counterWriter = common.NewDefaultCounterWriter(c.rip, c.rport)
	err = c.counterWriter.Init()
	if err != nil {
		log.Println("Error connect to redis instance,flow counter won't work")
	}

	//start ticker
	ticker := time.NewTicker(time.Duration(5) * time.Second)
	go func() {
		//test
		for {
			select {
			case <-ticker.C:
				//collect flow counter and write to redis
				var res int64
				for _, g := range c.workers {
					res += atomic.LoadInt64(&g.flowCounter)
				}
				err := c.counterWriter.Write(res)
				if err != nil {
					log.Println("Error write flow counter to redis")
				}
				continue
			case <-stopTickerChan:
				ticker.Stop()
				return
			}
		}
	}()

	return nil
}

func (c *controller) Start() error {
	for _, g := range c.workers {
		go g.Start()
	}

	c.waiter.Wait()
	err := c.counterWriter.Destroy()
	if err != nil {
		log.Println("Error write flow counter to redis")
	}
	log.Println("All work done, controller exits")
	return nil
}
