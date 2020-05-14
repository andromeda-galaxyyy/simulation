package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
)





func main(){
	id:=flag.Int("id",0,"self id")
	dstIdFn:=flag.String("dst_id","/tmp","destiantion id file")
	pktDir:=flag.String("pkts","/tmp/pkts","pkts dir")
	flag.Parse()

	if !FileExist(*dstIdFn){
		log.Fatal(fmt.Sprintf("File not exists %s\n", *dstIdFn))
	}
	if !DirExists(*pktDir){
		log.Fatal(fmt.Sprintf("Dir not exists %s\n", *pktDir))
	}
	dstIds:=make([]int,0)

	fp,err:=os.Open(*dstIdFn)
	if err!=nil{
		log.Fatal(err)
	}
	defer fp.Close()

	scanner:=bufio.NewScanner(fp)
	for scanner.Scan(){
		res,err:=strconv.Atoi(scanner.Text())
		if err!=nil{
			log.Fatal("Invalid destination id file")
		}
		dstIds=append(dstIds,res)
	}
	log.Println(fmt.Sprintf("#destination id file %d",len(dstIds)))

	generator:=Generator{
		SelfID:        *id,
		DestinationIDs: dstIds,
		PktsDir:       *pktDir,
	}
	err=generator.Start()
	if err!=nil{

	}

}