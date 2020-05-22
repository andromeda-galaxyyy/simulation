package utils

import (
	"encoding/json"
	"fmt"
	"net"
)

func SendByte(ip string,port int,content []byte) (err error)  {
	conn,err:=net.Dial("tcp",fmt.Sprintf("%s:%d",ip,port))
	if err!=nil{
		return err
	}
	defer conn.Close()
	_, err = conn.Write(content)

	return err

}

func SendStr(ip string,port int,content *string)(err error)  {
	return SendByte(ip,port,[]byte(*content))
}

func SendMap(ip string,port int,content map[string]interface{}) error  {
	jsonBytes,err:=json.Marshal(content)
	if err!=nil{
		return err
	}
	err= SendByte(ip,port,jsonBytes)
	return err
}