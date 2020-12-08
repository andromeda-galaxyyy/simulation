package main

import (
	"github.com/gin-gonic/gin"
	"net/http"
)

func GetFlowCounter(c *gin.Context)  {
	stats,err:=counterReader.Read()
	if err!=nil{
		c.JSON(http.StatusInternalServerError, gin.H{
			"msg":"Internel Error",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"res":stats,
	})
	return
}