package common

import (
	"chandler.com/gogen/utils"
	"context"
	"fmt"
	"github.com/go-redis/redis/v8"
	"log"
	"strconv"
)

type FCounterWriter struct {
	id int64
	ip string
	port int
	handle *redis.Client
}

func (w *FCounterWriter)Write(count int64) error {
	ctx:=context.Background()
	err:=w.handle.Set(ctx,fmt.Sprintf("%d",w.id),count,0).Err()
	if err!=nil{
		log.Println("FCounterWriter error when write flow counter")
		return err
	}
	return nil
}

func (w *FCounterWriter)Destroy() error{
	ctx:=context.Background()
	err:=w.handle.Del(ctx,fmt.Sprintf("%d",w.id)).Err()
	if err!=nil{
		return err
	}
	return nil
}

func (w *FCounterWriter)Init() error  {
	w.handle=redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%d",w.ip,w.port),
		DB:5,
	})
	ctx:=context.Background()
	_,err:=w.handle.Ping(ctx).Result()
	if err!=nil{
		log.Printf("FCounterWriter error connect to redis instance with %s:%d\n",w.ip,w.port)
		return err
	}
	log.Println("FCounterWriter connect to redis instance successfully")
	return nil
}

func NewDefaultCounterWriter(ip string,port int) *FCounterWriter {
	return &FCounterWriter{
		id: utils.NowInNano(),
		ip:ip,
		port:port,
	}
}

type FCounterReader struct {
	id int64
	ip string
	port int
	handle *redis.Client
}

func NewDefaultCounterReader(ip string,port int) *FCounterReader {
	return &FCounterReader{
		id:utils.NowInMilli(),
		ip:ip,
		port:port,
	}
}

func (r *FCounterReader)Init() error{
	r.handle=redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf(	"%s:%d",r.ip,r.port),
		DB:5,
	})
	ctx:=context.Background()
	_,err:=r.handle.Ping(ctx).Result()
	if err!=nil{
		log.Printf("FCounterReader Error when connect to redis instance with %s:%d\n",r.ip,r.port)
		return err
	}
	log.Println("FCounterReader connect to redis instance successfully")
	return nil
}

func (r *FCounterReader)Read() (int64,error) {
	ctx:=context.Background()
	var res int64=0
	//var n int
	var cursor uint64
	for {
		var keys []string
		var err error
		keys,cursor,err=r.handle.Scan(ctx,cursor,"1*",10).Result()
		if err!=nil{
			return 0,err
		}

		for _,key:=range keys{
			//get key
			tmp,err:=r.handle.Get(ctx,key).Result()
			if err!=nil{
				return 0,err
			}
			tmpRes,err:=strconv.Atoi(tmp)
			if err!=nil{
				panic(err)
			}
			res+= int64(tmpRes)
		}
		if cursor==0{
			// we come to the end of the set
			break
		}
	}
	return res,nil
}


