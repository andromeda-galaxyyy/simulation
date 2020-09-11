package main

import (
	"chandler.com/gogen/utils"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
	"log"
	"time"
)

var (
	ether *layers.Ethernet
	vlan *layers.Dot1Q
	ipv4 *layers.IPv4
	tcp *layers.TCP
	udp *layers.UDP
	payloadPerPacketSize int
	options gopacket.SerializeOptions
	fType int
)

type payloadManipulator func([]byte)
type payloadManipulators []payloadManipulator

func addTsManipulator(rawData []byte)  {
	for i:=0;i<9;i++{
		rawData[i]=byte(0)
	}
	nowMilliSeconds:=utils.Int64ToBytes(time.Now().UnixNano()/1e6)
	utils.Copy(rawData,0,nowMilliSeconds,0,8)
}

func indicateLastPayload(rawData []byte)  {
	rawData[8]=utils.SetBit(rawData[8],7)
}

func indicateNotLastPayload(rawData []byte)  {
	rawData[8]=utils.UnsetBit(rawData[8],7)
}




//todo indicate low latency or elephant flow

// 前8个byte记录时间戳，后一个byte最高位表示流是否结束，后几位表示流的种类，是否需要记录时间戳
func send(handle *pcap.Handle,buffer gopacket.SerializeBuffer,rawData []byte,payloadSize int,payloadPerPacketSize int ,ether *layers.Ethernet,vlan *layers.Dot1Q,ipv4 *layers.IPv4,tcp *layers.TCP,udp *layers.UDP,isTCP bool,addTs bool,lastPayload bool) (err error) {
	//payloadPerPacketSize:=g.MTU-g.EmptySize
	count:=payloadSize/payloadPerPacketSize

	payloadSizeBk:=payloadSize
	for i:=0;i<9;i++{
		rawData[i]=byte(0)
	}
	if fType>=4{
		log.Fatalf("Unsupported flow type:%d\n",fType)
	}

	var b=byte(fType)
	rawData[8]=b

	//buffer:=g.buffer
	for ;count>0;count--{
		//_ = buffer.Clear()
		payLoadPerPacket:=rawData[:payloadPerPacketSize]
		if addTs{
			nowMilliSeconds:=utils.Int64ToBytes(time.Now().UnixNano()/1e6)
			utils.Copy(payLoadPerPacket,0,nowMilliSeconds,0,8)
		}
		//如果是整数倍,而且这是最后一个
		if payloadSizeBk%payloadPerPacketSize==0&&count==1{
			if lastPayload{
				payLoadPerPacket[8]=utils.SetBit(payLoadPerPacket[8],7)
			}else{
				//log.Println("Unset bit")
				payLoadPerPacket[8]=utils.UnsetBit(payLoadPerPacket[8],7)
			}
		}

		payloadSize-=payloadPerPacketSize
		if isTCP{
			err=gopacket.SerializeLayers(buffer,options,ether,vlan,ipv4,tcp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return err
			}
			err=handle.WritePacketData(buffer.Bytes())
			if err!=nil{
				return err
			}
		}else{
			err=gopacket.SerializeLayers(buffer,options,ether,vlan,ipv4,udp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return err
			}
			err=handle.WritePacketData(buffer.Bytes())
			if err!=nil{
				return err
			}
		}
	}
	// send all we return
	if payloadSize==0{
		return nil
	}


	if payloadSize<9{
		payloadSize=9
	}

	leftPayload :=rawData[:payloadSize]
	if addTs{
		nowMilliSeconds:=utils.Int64ToBytes(time.Now().UnixNano()/1e6)
		utils.Copy(leftPayload,0,nowMilliSeconds,0,8)
	}

	if lastPayload{
		//log.Println("Last payload, Set bit")
		leftPayload[8]=utils.SetBit(leftPayload[8],7)
	}else{
		//log.Println("Unset bit")
		leftPayload[8]=utils.UnsetBit(leftPayload[8],7)
	}

	if isTCP{
		err=gopacket.SerializeLayers(buffer,options,ether,vlan,ipv4,tcp,gopacket.Payload(leftPayload))
		if err!=nil{
			return err
		}
		err=handle.WritePacketData(buffer.Bytes())
		if err!=nil{
			return err
		}
	}else{
		err=gopacket.SerializeLayers(buffer,options,ether,vlan,ipv4,udp,gopacket.Payload(leftPayload))
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

