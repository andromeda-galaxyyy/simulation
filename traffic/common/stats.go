package gogen

import "fmt"

const (
	IoT=iota
	Video
)


type FlowDesc struct {
	sport int
	dport int
	sip string
	dip string
	proto string

	startTs int64
	endTs int64
	flowType int
	packets int64

	minDelay    int64
	maxDelay    int64
	meanDelay   float64
	stdvarDelay float64
}


func (f *FlowDesc) ToLossRateStats() string{
	return fmt.Sprintf("%d %d %s %d %s %d %s %d %d",
		f.startTs,
		f.endTs,
		f.sip,
		f.sport,
		f.dip,
		f.dport,
		f.proto,
		f.flowType,
		f.packets,
	)
}

func (f *FlowDesc) ToDelayStats() string  {
	return fmt.Sprintf("%d %s %d %s %d %s %d %d %.2f %.2f",f.flowType,f.sip,f.sport, f.dip,f.dport,f.proto,f.minDelay,f.maxDelay,f.meanDelay,f.stdvarDelay)
}