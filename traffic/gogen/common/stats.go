package common

import (
	"errors"
	"fmt"
	"strconv"
	"strings"
)

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

	FlowType        int

	ReceivedPackets int64
	Loss            float64
	PeriodPackets   int64
	PeriodLoss      float64

	MinDelay    int64
	MaxDelay    int64
	MeanDelay   float64
	StdVarDelay float64
}



func (f *FlowDesc) ToRxLossStats() string{
	return fmt.Sprintf("%d %d %d %.2f %s %d %s %d %s %d",
		f.RxStartTs,
		f.RxEndTs,
		f.ReceivedPackets,
		f.PeriodLoss,
		f.SrcIP,
		f.SrcPort,
		f.DstIP,
		f.DstPort,
		f.Proto,
		f.FlowType,
	)
}


func DescFromRxLossStats(desc *FlowDesc,line string) error{
	if nil==desc{
		return errors.New("dst is nil")
	}
	contents:=strings.Split(line," ")
	if len(contents)!=9{
		return errors.New("error parsing line")
	}
	var err error
	desc.RxStartTs,err=strconv.ParseInt(contents[0],10,64)
	if err!=nil{
		return errors.New("error parsing line")
	}

	desc.RxEndTs,err=strconv.ParseInt(contents[1],10,64)
	if err!=nil{
		return errors.New("error parsing line")
	}

	desc.ReceivedPackets,err=strconv.ParseInt(contents[2],10,64)
	if err!=nil{
		return errors.New("error parsing line")
	}

	desc.PeriodLoss,err=strconv.ParseFloat(contents[3],10)
	if err!=nil{
		return errors.New("error parsing line")
	}

	desc.SrcIP=contents[4]
	desc.SrcPort,err=strconv.Atoi(contents[5])
	if err!=nil{
		return errors.New("error parsing line")
	}
	desc.DstIP=contents[6]
	desc.DstPort,err=strconv.Atoi(contents[7])
	if err!=nil{
		return errors.New("error parsing line")
	}
	desc.Proto=contents[8]
	desc.FlowType,err=strconv.Atoi(contents[9])
	if err!=nil{
		return errors.New("error parsing line")
	}
	return nil
}

func RxLossHeader() string{
	return "RxStartTs RxEndTs #packets #periodloss sip sport dip dport proto flowtype"
}

func (f *FlowDesc) ToTxLossStats() string{
	return fmt.Sprintf("%d %d %d %s %d %s %d %s %d",
		f.TxStartTs,
		f.TxEndTs,
		f.ReceivedPackets,
		f.SrcIP,
		f.SrcPort,
		f.DstIP,
		f.DstPort,
		f.Proto,
		f.FlowType,
	)
}
func TxLossHeader() string  {
	return "TxStartTs TxEndTs #packets sip sport dip dport proto flowtype"
}

func (f *FlowDesc) ToDelayStats() string  {
	return fmt.Sprintf("%d %d %s %d %s %d %s %d %d %.2f %.2f %d",
		f.RxStartTs,
		f.RxEndTs,
		f.SrcIP,
		f.SrcPort,
		f.DstIP,
		f.DstPort,
		f.Proto,
		f.MinDelay,
		f.MaxDelay,
		f.MeanDelay,
		f.StdVarDelay,
		f.FlowType,
	)
}

func DescFromDelayStats(desc *FlowDesc,line string) error  {
	if nil==desc{
		return errors.New("dst is nil")
	}
	contents:=strings.Split(line," ")
	if len(contents)!=12{
		return errors.New("error parsing line")
	}
	var err error
	desc.RxStartTs,err=strconv.ParseInt(contents[0],10,64)
	if err!=nil{
		return errors.New("error parsing line")
	}

	desc.RxEndTs,err=strconv.ParseInt(contents[1],10,64)
	if err!=nil{
		return errors.New("error parsing line")
	}

	desc.SrcIP=contents[2]
	desc.SrcPort,err=strconv.Atoi(contents[3])
	if err!=nil{
		return errors.New("error parsing line")
	}
	desc.DstIP=contents[4]
	desc.DstPort,err=strconv.Atoi(contents[5])
	if err!=nil{
		return errors.New("error parsing line")
	}
	desc.Proto=contents[6]
	desc.MinDelay,err=strconv.ParseInt(contents[7],10,64)
	if err!=nil{
		return errors.New("error parsing line")
	}
	desc.MaxDelay,err=strconv.ParseInt(contents[8],10,64)
	if err!=nil{
		return errors.New("error parsing line")
	}
	desc.MeanDelay,err=strconv.ParseFloat(contents[9],10)
	if err!=nil{
		return errors.New("error parsing line")
	}
	desc.StdVarDelay,err=strconv.ParseFloat(contents[10],10)
	if err!=nil{
		return errors.New("error parsing line")
	}

	desc.FlowType,err=strconv.Atoi(contents[11])
	if err!=nil{
		return errors.New("error parsing line")
	}
	return nil
}

func RxDelayStatsHeader()string  {
	return "RxStartTs RxEndTs sip sport dip dport proto min max mean stdvar flowtype"
}

func (f *FlowDesc) String() string{
	return fmt.Sprintf("start:%d,end:%d,ReceivedPackets:%d,SrcIP:%s,SrcPort:%d,DstPort:%s,DstPort:%d,proto:%s,flow_type:%d,min_delay:%d,max_delay:%d,mean_delay:%.2f,stdvar_delay:%.2f",
	f.TxStartTs,
	f.TxEndTs,
	f.ReceivedPackets,
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



type DetailedFlowDesc struct{
	SrcIP string
	SrcPort int
	DstIP string
	DstPort int
	Proto string


	TxStartTs int64
	TxEndTs   int64

	RxStartTs int64
	RxEndTs   int64

	FlowType int
	Delays []int64
}







