package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"context"
	"fmt"
	"github.com/go-redis/redis/v8"
	"log"
)

type Writer interface {
	Init() (err error)
	Start()
	Write(line string, ts int64) error
	BatchWrite(lines []string, ts int64) error
}

type redisWriter struct {
	ip        string
	port      int
	//handle0 and handle1 is for delay,src && dst respectively
	handle0   *redis.Client
	handle1 *redis.Client
	//handle2 and handle3 is for loss,src && dst respectively
	handle2 *redis.Client
	handle3 *redis.Client

	lossChan  chan string
	delayChan chan string
	fileChan  chan string
	doneChan  chan common.Signal
	// redis采用多副本，以src为key和以dst为key
	// 方便debug和查询

}

func NewDefaultRedisWriter(ip string,port int) *redisWriter {
	return &redisWriter{
		ip:        ip,
		port:      port,
		handle0:   nil,
		lossChan:  nil,
		delayChan: nil,
		fileChan:  nil,
		doneChan:  nil,
	}
}

func (r *redisWriter) Write(line string, ts int64) error {
	desc:=&common.FlowDesc{}
	err:=common.DescFromDelayStats(desc,line)
	if err!=nil{
		return err
	}
	srcIp:=desc.SrcIP
	srcId,err:=utils.IdFromIP(srcIp)
	if err!=nil{
		return err
	}
	dstIp:=desc.DstIP
	dstId,err:=utils.IdFromIP(dstIp)
	if err!=nil{
		return err
	}
	ctx:=context.Background()
	if err:=r.handle0.ZAdd(ctx,fmt.Sprintf("%d",srcId),&redis.Z{
		Score:  float64(ts),
		Member: line,
	}).Err();err!=nil{
		return err
	}

	if err:=r.handle1.ZAdd(ctx,fmt.Sprintf("%d",dstId),&redis.Z{
		Score:  float64(ts),
		Member: line,
	}).Err();err!=nil{
		return err
	}
	return nil
}

func (r *redisWriter)BatchWrite(lines []string, ts int64) error {
	for _,line:=range lines{
		_=r.Write(line,ts)
	}
	return nil
}

func (r *redisWriter) Init() error {
	r.handle0 =redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d",r.ip, r.port),
		Password: "",
		DB: 0,
	})
	ctx:=context.Background()
	_,err:=r.handle0.Ping(ctx).Result()
	if err!=nil{
		return err
	}

	r.handle1 =redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d",r.ip, r.port),
		Password: "",
		DB: 1,
	})
	//ctx:=context.Background()
	_,err=r.handle1.Ping(ctx).Result()
	if err!=nil{
		return err
	}

	r.handle2 =redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d",r.ip, r.port),
		Password: "",
		DB: 2,
	})
	_,err=r.handle2.Ping(ctx).Result()
	if err!=nil{
		return err
	}

	r.handle3 =redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d",r.ip, r.port),
		Password: "",
		DB: 3,
	})
	_,err=r.handle3.Ping(ctx).Result()
	if err!=nil{
		return err
	}

	return nil
}

func (r *redisWriter) Start() {
	if nil!=r.handle0 {
		defer r.handle0.Close()
	}
	//ctx:=context.Background()
	for {
		select {
		case <-r.doneChan:
			log.Println("Redis writer stop requested")
			return
		case  <-r.lossChan:
			continue
			//log.Printf("Redis writer loss file:%s\n", fn)
		case fn := <-r.delayChan:
			if !utils.IsFile(fn) {
				continue
			}

			log.Printf("delay file:%s\n", fn)
			lines, err := utils.ReadLines(fn)

			lines=lines[1:]

			if err != nil {
				log.Printf("Redis writer cannot read line from %s\n", fn)
				continue
			}
			ctime,_:=utils.GetCreateTimeInSec(fn)
			err=r.BatchWrite(lines, ctime)

			if err != nil {
				log.Printf("Redis writer cannot store %s\n", fn)
				continue
			}
		}
	}

}



