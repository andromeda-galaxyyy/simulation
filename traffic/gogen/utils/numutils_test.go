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

