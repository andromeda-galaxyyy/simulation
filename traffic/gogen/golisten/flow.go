package main

import "fmt"

type flowDesc struct {
	sport string
	dport string
	sip   string
	dip   string
	proto string
	//in milli
	minDelay    int64
	maxDelay    int64
	meanDelay   float64
	stdvarDelay float64

	flowType int
}

func (f *flowDesc)String() string {
	//return fmt.Sprintf("delay: min: %d, max :%d, mean :%.2f, stdvar :%2.f",)
	//sip,sport,dip,dport,proto
	return fmt.Sprintf("%d %s %s %s %s %s %d %d %.2f %.2f",f.flowType,f.sip,f.sport, f.dip,f.dport,f.proto,f.minDelay,f.maxDelay,f.meanDelay,f.stdvarDelay)
}


