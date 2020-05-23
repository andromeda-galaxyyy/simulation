package utils

import (
	"bytes"
	"errors"
	"fmt"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"log"
	"net"
	"strconv"
	"strings"
	"time"
)

var (
	rawBytes       [] byte
	buffer         gopacket.SerializeBuffer
	etherLayer     *layers.Ethernet
	ipv4Layer      *layers.IPv4
	tcpLayer       *layers.TCP
	udpLayer       *layers.UDP
	defaultOptions *gopacket.SerializeOptions
	err error
)

func init()  {
	buffer=gopacket.NewSerializeBuffer()
	defaultOptions=&gopacket.SerializeOptions{}
	defaultOptions.FixLengths=true
	etherLayer = &layers.Ethernet{
		EthernetType: 0x800,
	}
	ipv4Layer = &layers.IPv4{
		Version:    4,   //uint8
		IHL:        5,   //uint8
		TOS:        0,   //uint8
		Id:         0,   //uint16
		Flags:      0,   //IPv4Flag
		FragOffset: 0,   //uint16
		TTL:        255, //uint8
	}
	tcpLayer=&layers.TCP{}
	udpLayer=&layers.UDP{}
	rawBytes=make([]byte,1600)
}

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


func send(payloadSize int,ether *layers.Ethernet,ip *layers.IPv4,tcp *layers.TCP,udp *layers.UDP,isTCP bool,handle *pcap.Handle,options *gopacket.SerializeOptions) (err error){
	nowInMilli:=Int64ToBytes(time.Now().UnixNano()/1e6)
	log.Println(nowInMilli)
	Copy(rawBytes,0,nowInMilli,0,8)

	//log.Println(rawBytes[:payloadSize])

		if isTCP{
			err=gopacket.SerializeLayers(buffer,*options,ether,ip,tcp,gopacket.Payload(rawBytes[:payloadSize]))
			if err!=nil{
				return err
			}

			err=handle.WritePacketData(buffer.Bytes())
			if err!=nil{
				return err
			}
		}else{
			err=gopacket.SerializeLayers(buffer,*options,ether,ip,udp,gopacket.Payload(rawBytes[:payloadSize]))
			if err!=nil{
				return err
			}
			err=handle.WritePacketData(buffer.Bytes())
			if err!=nil{
				return err
			}
		}
	return nil
}

//a function to send raw bytes
//for test only
func Send(specifier [5]string,smac,dmac string,payloadSize int,handle *pcap.Handle) error {
	sport,err:=strconv.Atoi(specifier[0])
	if err!=nil{
		return err
	}
	dport,err:=strconv.Atoi(specifier[1])
	if err!=nil{
		return err
	}
	sip:=specifier[2]
	dip:=specifier[3]
	proto:=specifier[4]
	tcp:= proto=="TCP"
	srcMac,_:=net.ParseMAC(smac)
	dstMac,_:=net.ParseMAC(dmac)
	etherLayer.SrcMAC=srcMac
	etherLayer.DstMAC=dstMac

	ipv4Layer.SrcIP=net.ParseIP(sip)
	ipv4Layer.DstIP=net.ParseIP(dip)
	if tcp{
		ipv4Layer.Protocol=6
		tcpLayer.SrcPort=layers.TCPPort(sport)
		tcpLayer.DstPort=layers.TCPPort(dport)

	}else{
		ipv4Layer.Protocol=17
		udpLayer.SrcPort=layers.UDPPort(sport)
		udpLayer.DstPort=layers.UDPPort(dport)
	}
	return send(payloadSize,etherLayer,ipv4Layer,tcpLayer,udpLayer,tcp,handle,defaultOptions)
}