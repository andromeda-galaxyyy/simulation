package main

import (
	"chandler.com/gogen/utils"
	"github.com/google/gopacket"
	"log"
	"time"
)


// 前8个byte记录时间戳，后一个byte最高位表示流是否结束，后几位表示流的种类，是否需要记录时间戳
func (g *Generator)send(
	payloadSize int,
	isTCP bool,
	addTs bool,
	lastPayload bool) (err error) {
	count:=payloadSize/g.payloadPerPacketSize
	fType:=g.fType

	payloadSizeBk:=payloadSize
	for i:=0;i<9;i++{
		g.rawData[i]=byte(0)
	}
	if fType>=4{
		log.Fatalf("Unsupported flow type:%d\n",fType)
	}

	var b=byte(fType)
	g.rawData[8]=b

	//buffer:=g.buffer
	for ;count>0;count--{
		//_ = buffer.Clear()
		payLoadPerPacket:=g.rawData[:g.payloadPerPacketSize]

		//如果是整数倍,而且这是最后一个
		if payloadSizeBk%g.payloadPerPacketSize==0&&count==1{
			if lastPayload{
				payLoadPerPacket[8]=utils.SetBit(payLoadPerPacket[8],7)
			}else{
				//log.Println("Unset bit")
				payLoadPerPacket[8]=utils.UnsetBit(payLoadPerPacket[8],7)
			}
		}
		if addTs{
			nowMilliSeconds:=utils.Int64ToBytes(time.Now().UnixNano()/1e6)
			utils.Copy(payLoadPerPacket,0,nowMilliSeconds,0,8)
		}

		payloadSize-=g.payloadPerPacketSize
		if isTCP{
			err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.tcp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return err
			}
			err=g.handle.WritePacketData(g.buffer.Bytes())
			if err!=nil{
				return err
			}
		}else{
			err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.udp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return err
			}
			err=g.handle.WritePacketData(g.buffer.Bytes())
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

	leftPayload :=g.rawData[:payloadSize]


	if lastPayload{
		//log.Println("Last payload, Set bit")
		leftPayload[8]=utils.SetBit(leftPayload[8],7)
	}else{
		//log.Println("Unset bit")
		leftPayload[8]=utils.UnsetBit(leftPayload[8],7)
	}

	if addTs{
		nowMilliSeconds:=utils.Int64ToBytes(time.Now().UnixNano()/1e6)
		utils.Copy(leftPayload,0,nowMilliSeconds,0,8)
	}

	if isTCP{
		err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.tcp,gopacket.Payload(leftPayload))
		if err!=nil{
			return err
		}
		err=g.handle.WritePacketData(g.buffer.Bytes())
		if err!=nil{
			return err
		}
	}else{
		err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.udp,gopacket.Payload(leftPayload))
		if err!=nil{
			return err
		}
		err=g.handle.WritePacketData(g.buffer.Bytes())
		if err!=nil{
			return err
		}
	}

	return nil
}

func (g *Generator)sendSeq(
	isTCP bool,
	seqNum int64,
	) (err error){

	payload:=g.rawData[:9]
	defer func() {
		payload[8]=utils.UnsetBit(payload[8],2)
	}()
	//reset to zero
	for i:=0;i<9;i++{
		payload[i]=byte(0)
	}
	utils.Copy(payload,0,utils.Int64ToBytes(seqNum),0,8)
	// 第二位设置1
	payload[8]=utils.SetBit(payload[8],2)

	if isTCP{
		err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.tcp,gopacket.Payload(payload))
		if err!=nil{
			return err
		}
		err=g.handle.WritePacketData(g.buffer.Bytes())
		if err!=nil{
			return err
		}
		return nil

	}

	err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.udp,gopacket.Payload(payload))
	if err!=nil{
		return err
	}
	err=g.handle.WritePacketData(g.buffer.Bytes())
	if err!=nil{
		return err
	}

	return nil
}


/**
多了两个参数
lastSeqNum 上一次seq number
lastPeriodPktCount 当前周期发送的包数量

返回值：updatedPeriodPktCount 更新后的周期发送包数量
updatedSeqNum 更新后的seq number
err 错误

for example
lastSeqNum=2
lastPeriodPktCount=99

实际上发送了5个包
那么
updatedPeriodPktCount=103
updatedSeqNum=3

for example
lastSeqNum=2
lastPeriodPktCount=20
实际发送了一个包
那么
updatedPeriodPktCount=21
updatedSeqNum=2
 */
func (g *Generator)sendWithSeq(
	payloadSize int,
	isTCP bool,
	addTs bool,
	lastPayload bool,
	lastSeqNum int64,
	lastPeriodPktCount int64,
	) (updatedPeriodPktCount int64,updatedSeqNum int64,err error) {

	updatedPeriodPktCount=lastPeriodPktCount
	updatedSeqNum=lastSeqNum
	count:=payloadSize/g.payloadPerPacketSize

	payloadSizeBk:=payloadSize
	//fType:=g
	for i:=0;i<9;i++{
		g.rawData[i]=byte(0)
	}
	if g.fType>=4{
		log.Fatalf("Unsupported flow type:%d\n",g.fType)
	}

	var b=byte(g.fType)
	g.rawData[8]=b

	//buffer:=g.buffer
	for ;count>0;count--{
		//_ = buffer.Clear()
		payLoadPerPacket:=g.rawData[:g.payloadPerPacketSize]

		//如果是整数倍,而且这是最后一个
		if payloadSizeBk%g.payloadPerPacketSize==0&&count==1{
			if lastPayload{
				payLoadPerPacket[8]=utils.SetBit(payLoadPerPacket[8],7)
			}else{
				//log.Println("Unset bit")
				payLoadPerPacket[8]=utils.UnsetBit(payLoadPerPacket[8],7)
			}
		}

		payloadSize-=g.payloadPerPacketSize

		if addTs{
			nowMilliSeconds:=utils.Int64ToBytes(time.Now().UnixNano()/1e6)
			utils.Copy(payLoadPerPacket,0,nowMilliSeconds,0,8)
		}
		if isTCP{
			err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.tcp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return 0,0,err
			}
			err=g.handle.WritePacketData(g.buffer.Bytes())
			if err!=nil{
				return 0,0,err
			}
			updatedPeriodPktCount++
			if updatedPeriodPktCount%100==0{
				updatedSeqNum+=1
				_=g.sendSeq(isTCP,updatedSeqNum)
			}

		}else{
			err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.udp,gopacket.Payload(payLoadPerPacket))
			if err!=nil{
				return 0,0,err
			}
			err=g.handle.WritePacketData(g.buffer.Bytes())
			if err!=nil{
				return 0,0,err
			}
			updatedPeriodPktCount++
			if updatedPeriodPktCount%100==0{
				updatedSeqNum+=1
				_=g.sendSeq(isTCP,updatedSeqNum)
			}

		}
	}
	// send all we return
	if payloadSize==0{
		return updatedPeriodPktCount,updatedSeqNum,nil
	}


	if payloadSize<9{
		payloadSize=9
	}

	leftPayload :=g.rawData[:payloadSize]


	if lastPayload{
		//log.Println("Last payload, Set bit")
		leftPayload[8]=utils.SetBit(leftPayload[8],7)
	}else{
		//log.Println("Unset bit")
		leftPayload[8]=utils.UnsetBit(leftPayload[8],7)
	}

	if addTs{
		nowMilliSeconds:=utils.Int64ToBytes(time.Now().UnixNano()/1e6)
		utils.Copy(leftPayload,0,nowMilliSeconds,0,8)
	}
	if isTCP{
		err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.tcp,gopacket.Payload(leftPayload))
		if err!=nil{
			return 0,0,err
		}

		err=g.handle.WritePacketData(g.buffer.Bytes())
		if err!=nil{
			return 0,0,err
		}
		updatedPeriodPktCount++
		if updatedPeriodPktCount%100==0{
			updatedSeqNum+=1
			_=g.sendSeq(isTCP,updatedSeqNum)
		}
	}else{
		err=gopacket.SerializeLayers(g.buffer,g.options,g.ether,g.vlan,g.ipv4,g.udp,gopacket.Payload(leftPayload))
		if err!=nil{
			return 0,0,err
		}
		err=g.handle.WritePacketData(g.buffer.Bytes())
		if err!=nil{
			return 0,0,err
		}
		updatedPeriodPktCount++
		if updatedPeriodPktCount%100==0{
			updatedSeqNum+=1
			_=g.sendSeq(isTCP,updatedSeqNum)
		}
	}

	return updatedPeriodPktCount,updatedSeqNum,nil
}

