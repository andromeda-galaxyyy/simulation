package utils

import (
	"encoding/binary"
	"log"
	"math"
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

/**
start from zero
 */
func SetBit(b byte,n int) byte{
	if n>=8{
		log.Fatalf("n cannot greater than 7, given %d\n",n)
	}
	return b|(1<<n)
}

func SetBits(b byte,poss []int) byte{
	for pos:=range poss{
		if pos>=8{
			log.Fatalf("n cannot greater than 7, given %d\n",pos)
		}
		b=b|(1<<pos)
	}
	return b
}

func UnsetBit(b byte,n int)byte{
	if n>=8{
		log.Fatalf("n cannot greater than 7, given %d\n",n)
	}
	mask := ^(1 << n)
	b &= byte(mask)
	return b
}

func UnsetBits(b byte,poss []int)byte  {
	for pos:=range poss{
		if pos>=8{
			log.Fatalf("n cannot greater than 7, given %d\n",pos)
		}
		mask := ^(1 << pos)
		b&=byte(mask)
	}
	return b
}

func GetBit(b byte,n int) byte  {
	if n>=8{
		log.Fatalf("n cannot greater than 7, given %d\n",n)
	}
	return (b&(1<<n))>>n
}

func MinMax(nums []int64)(min,max int64)  {
	min=math.MaxInt64
	max=math.MinInt64
	for _,v:=range nums{
		if v>max{
			max=v
		}
		if v<min{
			min=v
		}
	}
	return min,max
}

func Average(nums []int64)  {

}

