package utils

import (
	"fmt"
	"testing"
)

func TestFileExist(t *testing.T) {
	fn:="/tmp/pkts/pkts.pkts"
	if FileExist(fn){
		fmt.Println("yes")
	}else{
		t.Fatal("wrong answer")
	}

	fn="/tmp/pkts/pktss"
	if FileExist(fn){
		t.Fatal("wrong answer")
	}else{
		fmt.Println("yes")
	}
}

func TestDirExists(t *testing.T) {
	dirFn:="/tmp/pkts"
	if !DirExists(dirFn){
		t.Fatal("Wrong")
	}
	dirFn="/tmp/hellodfd"
	if DirExists(dirFn){
		t.Fatal("wrong")
	}
}
func TestReadLines(t *testing.T) {
	lines,err:= ReadLines("/tmp/pkts/pkts.pkts")
	if err!=nil{
		t.Fatal("Wrong!")
	}else{
		fmt.Println(len(lines))
		fmt.Println(lines[0])
	}
}