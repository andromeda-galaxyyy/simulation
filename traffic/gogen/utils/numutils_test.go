package utils

import (
	"fmt"
	"testing"
)

func TestInt64ToBytes(t *testing.T) {
	bytes:=Int64ToBytes(1)
	fmt.Println(bytes)
	n:=BytesToInt64(bytes)
	fmt.Println(n)
	bytes=Int64ToBytes(-1)
	fmt.Println(bytes)
	n=BytesToInt64(bytes)
	fmt.Println(n)
}

func TestSetBit(t *testing.T) {
	b:=byte(0)
	b=SetBit(b,7)
	fmt.Println(b)
	fmt.Println(GetBit(b,7)==1)
	b=UnsetBit(b,7)
	fmt.Println(b)
	fmt.Println(GetBit(b,7))
}

func TestGetBit(t *testing.T) {
	b:=byte(128)
	fmt.Println(GetBit(b,7)==1)
	b=byte(127)
	fmt.Println(GetBit(b,7)==0)
}

