package utils

import "encoding/binary"

func Int64ToBytes(num int64) (res []byte) {
	res=make([]byte,8)
	binary.LittleEndian.PutUint64(res,uint64(num))
	return res
}

func BytesToInt64(bytes []byte)(res int64)  {
	res=int64(binary.LittleEndian.Uint64(bytes))
	return res
}
