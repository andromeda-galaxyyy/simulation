package main

import "github.com/gin-gonic/gin"

var (
	router *gin.Engine
)

func GinHelloWorld(context *gin.Context)  {
	context.JSON(200,gin.H{
		"message":"helloworld",
	})
}