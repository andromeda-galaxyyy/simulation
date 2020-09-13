package main

import (
	"chandler.com/gogen/utils"
	"context"
	"github.com/go-redis/redis/v8"
	"testing"
)

func TestRedisWriter_Write(t *testing.T) {
	lines:=[]string{"fuck","yes"}
	now:=utils.NowInNano()
	handle:=redis.NewClient(&redis.Options{
		Addr: "10.211.55.2:6379",
		DB:0,
	})
	ctx:=context.Background()
	for _,line:=range lines{
		handle.ZAdd(ctx,"test",&redis.Z{
			Score:  float64(now),
			Member: line,
		})
	}
}