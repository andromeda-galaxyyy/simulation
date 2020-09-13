package main

import (
	"chandler.com/gogen/common"
	"chandler.com/gogen/utils"
	"context"
	"fmt"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"log"
)

type MongoInitiator func(ctx context.Context, client *mongo.Client)

func DefaultInitiator(ctx context.Context,client *mongo.Client)  {
	for _,dbname:=range []string{"loss","delay"}{
		db:=client.Database(dbname)
		err:=db.Drop(ctx)
		if err!=nil{
			log.Fatalf("%s error drop db %s %s\n","MongoWriter",dbname,err)
		}

		log.Printf("%s drop db %s successfully\n","MongoWriter",dbname)
		for i:=0;i<66;i++{
			err:=db.CreateCollection(ctx,fmt.Sprintf("stats%d",i))
			if err!=nil{
				log.Fatalf("Cannot create collection stats%d\n",i)
			}
		}
	}
}


type MongoWriter struct {
	delayChan chan string
	lossChan chan string
	fileChan chan string
	done chan common.Signal
	ip string
	port int
	client *mongo.Client
	initiator MongoInitiator
}

func (writer *MongoWriter)String() string {
	return "MongoWriter"
}

func NewMongoWriter(ip string,port int) *MongoWriter {
	return &MongoWriter{
		ip: ip,
		port: port,
	}
}

func (writer *MongoWriter)Init()  {
	client,err:=mongo.NewClient(options.Client().ApplyURI(fmt.Sprintf("mongodb://%s:%d",writer.ip,writer.port)))
	if err!=nil{
		log.Fatalf("Mongowriter cannot connect to %s:%d",writer.ip,writer.port)
	}
	writer.client=client
}

func (writer *MongoWriter)Write(line string)error  {
	return nil
}

func (writer *MongoWriter)Start()  {
	//ctx=context.WithTimeout(context.Background())
	ctx:=context.Background()
	err:=writer.client.Connect(ctx)
	if err!=nil{
		log.Fatalf("Mongowriter cannot connect to %s:%d",writer.ip,writer.port)
	}
	defer writer.client.Disconnect(ctx)

	log.Println("Connect to mongo successfully")

	defer func() {
		if err = writer.client.Disconnect(ctx); err != nil {
			panic(err)
		}
	}()

	writer.initiator(ctx,writer.client)



	for{
		select {
		case <-writer.done:
			log.Println("MongoWriter stop requested")
			return
		case fn:=<-writer.lossChan:
			log.Printf("loss file:%s\n",fn)
		case fn:=<-writer.delayChan:
			if !utils.IsFile(fn){
				continue
			}
			//lines,err:=utils.ReadLines(fn)
			if err!=nil{
				log.Printf("MongoWriter cannot read line from %s\n",fn)
				continue
			}


			log.Printf("delay file:%s\n",fn)

		}
	}
}
