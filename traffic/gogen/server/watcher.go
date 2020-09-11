package main

import "log"

type Watcher struct {

}

func (w *Watcher) Init()  {
	log.Println("Watcher initiated")
}
