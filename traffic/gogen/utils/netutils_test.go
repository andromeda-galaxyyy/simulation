package utils

import (
	"fmt"
	"log"
	"testing"
)
func TestNetUtils_GenerateIP(t *testing.T)  {
	ids:=[]int{1,2,3,4,5,6,7,254,255,256,10000}
	for _,id:=range ids{
		ip,err:= GenerateIP(id)
		if err!=nil{
			log.Fatalln(err)
		}
		fmt.Println(ip)
	}
}

func TestNetUtils_GenerateMAC(t *testing.T)  {

	ids:=[]int{0,1,2,3,4,5,6,7,10,256}
	for _,id:=range ids{
		mac,err:= GenerateMAC(id)
		if err!=nil{
			log.Fatalln(err)
		}
		fmt.Println(mac)
	}
}