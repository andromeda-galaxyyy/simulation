package main

import (
	"context"
	"fmt"
	"github.com/go-redis/redis/v8"
)

type redisWriter struct {
	ip string
	port int
	handle *redis.Client
}

func newDefaultRedisWriter(ip string,port int) *redisWriter {
	return &redisWriter{
		ip:     ip,
		port:   port,
		handle: nil,
	}
}

func (writer *redisWriter)Init()(err error)  {
	writer.handle=redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d",writer.ip,writer.port),
		Password: "",
		DB:6,
	})
	ctx:=context.Background()
	_,err=writer.handle.Ping(ctx).Result()
	if err!=nil{
		fmt.Println("error when connect to redis instance")
		return err
	}
	return nil
}

func (writer *redisWriter)Write(r *result) error{
	return nil
	//ctx:=context.Background()
	//if err:
}


