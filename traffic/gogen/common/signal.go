package common

const FlushSignalType =1
const StopSignalType =2

type Signal struct {
	Type int
}

var FlushSignal=Signal{Type: FlushSignalType}
var StopSignal=Signal{Type: StopSignalType}

func IsFlushSig(sig Signal) bool  {
	return sig.Type==FlushSignal.Type
}

func IsStopSignal(sig Signal) bool  {
	return sig.Type==StopSignal.Type
}
