package main

import "net"

func SendByte(ip *string,port int,content []byte) (err error)  {
	conn,err:=net.Dial("tcp",*ip)
	if err!=nil{
		return err
	}
	defer conn.Close()
	_, err = conn.Write(content)

	return err

}

func SendStr(ip *string,port int,content *string)(err error)  {
	return SendByte(ip,port,[]byte(*content))
}