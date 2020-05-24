package utils

import (
	"encoding/binary"
	"log"
)

func Int64ToBytes(num int64) (res []byte) {
	res=make([]byte,8)
	binary.LittleEndian.PutUint64(res,uint64(num))
	return res
}

func BytesToInt64(bytes []byte)(res int64)  {
	res=int64(binary.LittleEndian.Uint64(bytes))
	return res
}

func SetBit(b byte,n int) byte{
	if n>=8{
		log.Fatalf("n cannot greater than 7, given %d\n",n)
	}
	return b|(1<<n)
}

func UnsetBit(b byte,n int)byte{
	if n>=8{
		log.Fatalf("n cannot greater than 7, given %d\n",n)
	}
	mask := ^(1 << n)
	b &= byte(mask)
	return b
}

func GetBit(b byte,n int) byte  {
	if n>=8{
		log.Fatalf("n cannot greater than 7, given %d\n",n)
	}
	return (b&(1<<n))>>n
}