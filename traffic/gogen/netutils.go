package main

import (
	"bytes"
	"fmt"
	"errors"
	"strings"
)

func GenerateIP(id int) (string,error){
	id++
	if 1<=id&&id<=254{
		return "10.0.0."+string(id),nil
	}
	if 255<=id && id<=255*254+253{
		return "10.0"+string(id/254)+"."+string(id%254),nil
	}
	fmt.Println("wrong")
	return "",errors.New("cannot support id addresss given a too large id")

}

func reverse(strs []string){
	for i:=len(strs)/2-1;i>=0;i--{
		opp:=len(strs)-1-i
		strs[i],strs[opp]=strs[opp],strs[i]
	}
}

//convert int to base 16 string
func base16(num int) string{
	res:=make([]string,0)
	if num==0{
		return ""
	}
	left:=0

	char:='a'
	for ;num>0;num/=16{
		left=num%16
		if left<10{
			res=append(res,string(left))
		}else{
			res=append(res,string(left-int(char)))
		}
	}
	reverse(res)
	return strings.Join(res,"")
}

func reverseStr(s string)string{
	res:=""
	for _,v:=range s{
		res=string(v)+res
	}
	return res
}

func GenerateMAC(id int)(string,error){
	id++
	raw_str:=base16(id)
	if len(raw_str)>12{
		return "",errors.New("Invalid id")
	}
	raw_str=reverseStr(raw_str)
	to_complete:=12-len(raw_str)

	for ;to_complete>0;to_complete--{
		raw_str+="0"
	}
	//every two elements
	var buffer bytes.Buffer
	for i,rune:=range raw_str{
		buffer.WriteRune(rune)
		if i%2==1 &&i!=len(raw_str){
			buffer.WriteRune(':')
		}
	}
	return buffer.String(),nil
}