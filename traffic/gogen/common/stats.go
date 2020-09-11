package common

// 导入包
import "fmt"

const (
	IoT=iota
	Video
)

// 流描述的结构体
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

/*各种与流描述相关的方法
*/
func (f *FlowDesc) ToRxLossStats() string{
	return fmt.Sprintf("%d %d %d %s %d %s %d %s %d",
		f.RxStartTs,
		f.RxEndTs,
		f.Packets,
		f.SrcIP,
		f.SrcPort,
		f.DstIP,
		f.DstPort,
		f.Proto,
		f.FlowType,
	)
}
func RxLossHeader() string{
	return "RxStartTs RxEndTs #packets sip sport dip dport proto flowtype"
}

func (f *FlowDesc) ToTxLossStats() string{
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
func TxLossHeader() string  {
	return "TxStartTs TxEndTs #packets sip sport dip dport proto flowtype"
}

func (f *FlowDesc) ToDelayStats() string  {
	return fmt.Sprintf("%s %d %s %d %s %d %d %.2f %.2f %d",
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
func RxDelayStatsHeader()string  {
	return "sip sport dip dport proto min max mean stdvar flowtype"
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


