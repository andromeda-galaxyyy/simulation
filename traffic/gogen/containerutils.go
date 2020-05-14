package main

type void struct {}
var dumb void

type StringSet struct {
	content map[string]void
}

func (set *StringSet)init(){
	set.content=make(map[string]void)
}
func (set *StringSet)Add(s string)  {
	set.content[s]=dumb
}
func (set *StringSet)Del(s string)  {
	delete(set.content,s)
}
func (set *StringSet)Contains(s string) bool {
	_,exits:=set.content[s]
	return exits
}

type IntSet struct {
	content map[int] void
}

func (set *IntSet) init()  {
	set.content= make(map[int]void)
}

func (set *IntSet)Add(i int)  {
	set.content[i]=dumb
}
func (set *IntSet)Del(i int)  {
	delete(set.content,i)
}

func (set *IntSet)Contains(i int)  bool {
	_,exits:=set.content[i]
	return exits
}



