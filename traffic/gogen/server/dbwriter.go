package main

import "chandler.com/gogen/common"

//  parse file into sqlite
type DBWriter struct {
	dbFile string
	delayChan chan string
	lossChan chan string
	fileChan chan string
	done chan common.Signal
}

func NewSqliteWriter(dbPath string) *DBWriter {
	return &DBWriter{
		dbFile: dbPath,
	}
}

func NewDefaultSqliteWriter() *DBWriter {
	return NewSqliteWriter("/tmp/db.sqlite")
}



func (writer *DBWriter)Init()  {

}

func (writer *DBWriter)Start(){
}

func (writer *DBWriter)parseAndStore(fPath string)(e error)  {
	return nil
}
