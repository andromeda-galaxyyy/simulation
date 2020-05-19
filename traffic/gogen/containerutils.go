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

func NewStringSet() *StringSet  {
	return &StringSet{
		content: make(map[string]void),
	}
}

type IntSet struct {
	content map[int] void
}

func NewIntSet() *IntSet {
	return &IntSet{
		content: make(map[int]void),
	}
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

func CopySlice(src []float64) (dst []float64)  {
	dst=make([]float64,len(src))
	for idx,v:=range src{
		dst[idx]=v
	}
	return dst
}

func CopyMap(m map[string][]float64) (dst map[string][]float64)  {
	dst=make(map[string][]float64)
	for k,v:=range m{
		dst[k]=CopySlice(v)
	}
	return dst
}

func FilterFloat(nums []float64,test func(float64) bool) (filtered []float64){
	for _,v:=range nums{
		if !test(v){
			continue
		}
		filtered=append(filtered,v)
	}
	return nums
}


//func CopyMap(m map[string]interface{}) map[string]interface{} {
//	cp := make(map[string]interface{})
//	for k, v := range m {
//		vm, ok := v.(map[string]interface{})
//		if ok {
//			cp[k] = CopyMap(vm)
//		} else {
//			cp[k] = v
//		}
//	}
//
//	return cp
//}

