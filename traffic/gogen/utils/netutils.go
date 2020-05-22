package utils

import (
	"bytes"
	"errors"
	"fmt"
	"strings"
)

func GenerateIP(id int) (string,error){
	id++
	if 1<=id&&id<=254{
		return fmt.Sprintf("10.0.0.%d",id),nil
		//return "10.0.0."+string(id),nil
	}
	if 255<=id && id<=255*254+253{
		//return "10.0."+string(id/254)+"."+string(id%254),nil
		return fmt.Sprintf("10.0.%d.%d",id/254,id%254),nil
	}
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
		return "0"
	}
	left:=0

	char:='a'
	for ;num>0;num/=16{
		left=num%16
		if left<10{
			res=append(res,fmt.Sprintf("%d",left) )
		}else{
			res=append(res,string(left-10+int(char)))
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
	rawStr := base16(id)
	//fmt.Println("raw str ",rawStr)
	if len(rawStr)>12{
		return "",errors.New("Invalid id")
	}
	rawStr = reverseStr(rawStr)
	toComplete :=12-len(rawStr)

	for ; toComplete >0; toComplete--{
		rawStr +="0"
	}
	rawStr= reverseStr(rawStr)
	//every two elements
	var buffer bytes.Buffer
	for i, r :=range rawStr {
		buffer.WriteRune(r)
		if i%2==1 &&i!=len(rawStr)-1{
			buffer.WriteRune(':')
		}
	}
	return buffer.String(),nil
}