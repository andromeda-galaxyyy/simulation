package common

import "fmt"

const (
	IoT=iota
	Video
)


type FlowDesc struct {
	SrcIP   string
	SrcPort int
	DstIP string
	DstPort int
	Proto   string

	TxStartTs int64
	TxEndTs   int64

	RxStartTs int64
	RxEndTs   int64

	FlowType int
	Packets  int64

	MinDelay    int64
	MaxDelay    int64
	MeanDelay   float64
	StdVarDelay float64
}


func (f *FlowDesc) ToLossRateStats() string{
	return fmt.Sprintf("%d %d %d %s %d %s %d %s %d",
		f.TxStartTs,
		f.TxEndTs,
		f.Packets,
		f.SrcIP,
		f.SrcPort,
		f.DstIP,
		f.DstPort,
		f.Proto,
		f.FlowType,
	)
}

func (f *FlowDesc) ToDelayStats() string  {
	return fmt.Sprintf("%d %s %d %s %d %s %d %d %.2f %.2f",
		f.FlowType,
		f.SrcIP,
		f.SrcPort,
		f.DstIP,
		f.DstPort,
		f.Proto,
		f.MinDelay,
		f.MaxDelay,
		f.MeanDelay,
		f.StdVarDelay,
	)
}

func (f *FlowDesc) String() string{
	return fmt.Sprintf("start:%d,end:%d,Packets:%d,SrcIP:%s,SrcPort:%d,DstPort:%s,DstPort:%d,proto:%s,flow_type:%d,min_delay:%d,max_delay:%d,mean_delay:%.2f,stdvar_delay:%.2f",
	f.TxStartTs,
	f.TxEndTs,
	f.Packets,
	f.SrcIP,
	f.SrcPort,
	f.DstIP,
	f.DstPort,
	f.Proto,
	f.FlowType,
	f.MinDelay,
	f.MaxDelay,
	f.MeanDelay,
	f.StdVarDelay,
	)
}


