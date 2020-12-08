package main

import (
	"context"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
)

var (
	telemetryHandle *redis.Client
)

func TelemetryFunc(isDelay bool) func(c *gin.Context)  {
	var keyTemplate string
	if isDelay{
		keyTemplate="%s-%s.delay"
	}else{
		keyTemplate="%s-%s.loss"
	}
	return func(c *gin.Context) {
		u,ok:=c.GetQuery("u")
		if !ok{
			c.JSON(http.StatusBadRequest, invalidRequestJSON)
			return
		}
		v,ok:=c.GetQuery("v")
		if !ok{
			c.JSON(http.StatusBadRequest,invalidRequestJSON)
			return
		}
		var count int64=5
		countStr,ok:=c.GetQuery("count")
		if ok{
			co,err:=strconv.ParseInt(countStr,10,64)
			if err!=nil{
				c.JSON(http.StatusBadRequest,invalidRequestJSON)
				return
			}
			count=co
		}

		key:=fmt.Sprintf(keyTemplate,u,v)
		ctx:=context.Background()
		delays,err:=telemetryHandle.ZRangeByScore(ctx,key,&redis.ZRangeBy{
			Min: "-inf",
			Max:"+inf",
			Count: count,
		}).Result()

		if err!=nil{
			c.JSON(http.StatusInternalServerError,internalErrorJSON)
			return
		}
		res:=make([]float64,0)
		for _,delayStr:=range delays{
			d,err:=strconv.ParseFloat(delayStr,64)
			if err!=nil{
				continue
			}
			res=append(res,d)
		}
		c.JSON(http.StatusOK, gin.H{
			"count":len(res),
			"res":res,
		})
		return
	}
}
//
//func GetLinkDelay(c *gin.Context){
//	u,ok:=c.GetQuery("u")
//	if !ok{
//		c.JSON(http.StatusBadRequest, invalidRequestJSON)
//		return
//	}
//	v,ok:=c.GetQuery("v")
//	if !ok{
//		c.JSON(http.StatusBadRequest,invalidRequestJSON)
//		return
//	}
//	var count int64=5
//	countStr,ok:=c.GetQuery("count")
//	if ok{
//		co,err:=strconv.ParseInt(countStr,10,64)
//		if err!=nil{
//			c.JSON(http.StatusBadRequest,invalidRequestJSON)
//			return
//		}
//		count=co
//	}
//
//	key:=fmt.Sprintf("%s-%s.delay",u,v)
//	ctx:=context.Background()
//	delays,err:=telemetryHandle.ZRangeByScore(ctx,key,&redis.ZRangeBy{
//		Min: "-inf",
//		Max:"+inf",
//		Count: count,
//	}).Result()
//
//	if err!=nil{
//		c.JSON(http.StatusInternalServerError,internalErrorJSON)
//		return
//	}
//	res:=make([]float64,0)
//	for _,delayStr:=range delays{
//		d,err:=strconv.ParseFloat(delayStr,64)
//		if err!=nil{
//			continue
//		}
//		res=append(res,d)
//	}
//	c.JSON(http.StatusOK, gin.H{
//		"count":len(res),
//		"res":res,
//	})
//	return
//}
//
//func GetLinkLoss(context *gin.Context)  {
//	context.JSON(http.StatusOK,gin.H{
//		"msg":"link loss",
//	})
//	return
//}


