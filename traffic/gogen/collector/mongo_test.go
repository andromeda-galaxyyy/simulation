package main


import (
	"testing"
)

func TestMongoWriter_Init(t *testing.T) {
	writer:=&MongoWriter{
		delayChan: nil,
		lossChan:  nil,
		fileChan:  nil,
		done:      nil,
		ip:        "localhost",
		port:      27017,
		client:    nil,
		initiator: DefaultInitiator,
	}
	writer.Init()
	writer.Start()
}
