package main

import (
	"chandler.com/gogen/utils"
	"testing"
	"time"
)

func TestWriter_Accept(t *testing.T) {
	channel:=make(chan *flowDesc,1024)
	utils.RmDir("/tmp/hello")
	_ = utils.CreateDir("/tmp/hello")

	w:=NewDefaultWriter(1,"/tmp/hello",channel)
	go w.Accept()
	f:=&flowDesc{
		sport:       "1",
		dport:       "2",
		sip:         "10.0.0.1",
		dip:         "10.0.0.2",
		proto:       "TCP",
		minDelay:    1,
		maxDelay:    2,
		meanDelay:   3,
		stdvarDelay: 4,
		flowType:    1,
	}
	for{
		channel<-f
		time.Sleep(time.Duration(500)*time.Millisecond)
	}
}
