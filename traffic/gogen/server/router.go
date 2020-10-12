package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"context"
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/go-redis/redis/v8"
	"log"
	"net/http"
	"strconv"
)

var (
	router *gin.Engine
	invalidRequestJSON=gin.H{
		"message":"invalid request",
	}
	internalErrorJSON=gin.H{
		"message":"internal error",
	}
	delayHandle0 *redis.Client
	delayHandle1 *redis.Client
	lossHandle0 *redis.Client
	lossHandle1 *redis.Client

	lossHandle   *redis.Client
)



func GinHelloWorld(context *gin.Context)  {
	context.JSON(200,gin.H{
		"message":"helloworld",
	})
}

func GetDelayBetween(c *gin.Context)  {
	from,ok:= c.GetQuery("from")
	if !ok{
		c.JSON(http.StatusBadRequest,invalidRequestJSON)
		return
	}
	start,err:=strconv.ParseInt(from,10,64)
	if err!=nil{
		c.JSON(http.StatusBadRequest,invalidRequestJSON)
		return
	}

	to,ok:= c.GetQuery("to")
	if !ok{
		c.JSON(http.StatusBadRequest,invalidRequestJSON)
		return
	}
	end,err:=strconv.ParseInt(to,10,64)
	if err!=nil{
		c.JSON(http.StatusBadRequest,invalidRequestJSON)
		return
	}
	ctx:=context.Background()

	src,srcExists:=c.GetQuery("src")

	dest,destExists:=c.GetQuery("dst")

	if srcExists||destExists{
		// src exists
		if srcExists{
			vals,err:= delayHandle0.ZRangeByScore(ctx,src,&redis.ZRangeBy{
				Min:    fmt.Sprintf("%d",start),
				Max:   fmt.Sprintf("%d",end),
			}).Result()
			if err!=nil{
				c.JSON(http.StatusInternalServerError,internalErrorJSON)
				return
			}
			tmp_res:=make([]interface{},0)
			for _,val:=range vals{
				desc:=&common.FlowDesc{}
				err=common.DescFromDelayStats(desc,val)
				if err!=nil{
					c.JSON(http.StatusInternalServerError,internalErrorJSON)
					return
				}
				tmp_res=append(tmp_res,desc)
			}
			filtered :=make([]interface{},0)
			if destExists{
				expectedDestId,err:=strconv.Atoi(dest)
				if err!=nil{
					c.JSON(http.StatusInternalServerError,internalErrorJSON)
					return
				}
				utils.Filter(&filtered,&tmp_res, func(e interface{}) bool {
					desc:=e.(*common.FlowDesc)
					did,_:=utils.IdFromIP(desc.DstIP)
					if did==expectedDestId{
						return true
					}
					return false
				})
			}else{
				filtered=tmp_res
			}
			log.Println(len(filtered))
			res:=make([]*common.FlowDesc,0)
			for _,d:=range filtered{
				res=append(res,d.(*common.FlowDesc))
			}
			c.JSON(http.StatusOK,gin.H{
				"num":len(res),
				"data":res,
			})
			return
		}else{
			//dst exists
			vals,err:= delayHandle1.ZRangeByScore(ctx,dest,&redis.ZRangeBy{
				Min:    fmt.Sprintf("%d",start),
				Max:   fmt.Sprintf("%d",end),
			}).Result()
			if err!=nil{
				c.JSON(http.StatusInternalServerError,internalErrorJSON)
				return
			}
			res:=make([]*common.FlowDesc,0)
			for _,v:=range vals{
				desc:=&common.FlowDesc{}
				common.DescFromDelayStats(desc,v)
				res=append(res,desc)
			}
			c.JSON(http.StatusOK,gin.H{
				"num":len(res),
				"data":res,
			})
			return
		}

	}
}