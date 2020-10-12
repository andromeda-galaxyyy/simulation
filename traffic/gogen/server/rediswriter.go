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
	ip string
	port int
	handle *redis.Client
	lossChan chan string
	delayChan chan string
	fileChan chan string
	doneChan chan common.Signal
	// redis采用多副本，以src为key和以dst为key
	// 方便debug和查询

}

func NewDefaultRedisWriter(ip string,port int) *redisWriter {
	return &redisWriter{
		ip:       ip,
		port:      port,
		handle:    nil,
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
	if err:=r.handle.ZAdd(ctx,fmt.Sprintf("%d",srcId),&redis.Z{
		Score:  float64(ts),
		Member: line,
	}).Err();err!=nil{
		return err
	}

	if err:=r.handle.ZAdd(ctx,fmt.Sprintf("%d",dstId),&redis.Z{
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
	r.handle=redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d",r.ip, r.port),
		Password: "",
		DB: 0,
	})
	ctx:=context.Background()
	_,err:=r.handle.Ping(ctx).Result()
	if err!=nil{
		return err
	}
	return nil
}

func (r *redisWriter) Start() {
	if nil!=r.handle{
		defer r.handle.Close()
	}
	//ctx:=context.Background()
	for {
		select {
		case <-r.doneChan:
			log.Println("Redis writer stop requested")
			return
		case fn := <-r.lossChan:
			log.Printf("Redis writer loss file:%s\n", fn)
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



