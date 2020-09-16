package utils

import (
	"math/rand"
)

type void struct {}
var dumb void

type StringSet struct {
	content map[string]void
}

func (set *StringSet)init(){
	set.content=make(map[string]void)
}
func (set *StringSet)Add(s string)  {
	set.content[s]= dumb
}
func (set *StringSet)Del(s string)  {
	delete(set.content,s)
}
func (set *StringSet)Contains(s string) bool {
	_,exits:=set.content[s]
	return exits
}


func NewStringSet() *StringSet {
	return &StringSet{
		content: make(map[string]void),
	}
}

type IntSet struct {
	content map[int]void
}

func NewIntSet() *IntSet {
	return &IntSet{
		content: make(map[int]void),
	}
}

func (set *IntSet) Init()  {
	set.content= make(map[int]void)
}

func (set *IntSet)Add(i int)  {
	set.content[i]= dumb
}
func (set *IntSet)Del(i int)  {
	delete(set.content,i)
}

func (set *IntSet)Contains(i int)  bool {
	_,exits:=set.content[i]
	return exits
}

type SpecifierSet struct {
	content map[[5]string]void
}

func (set *SpecifierSet)Contains(specifier *[5]string) bool  {
	_,exsits:=set.content[*specifier]
	return exsits
}
func (set *SpecifierSet)Add(specifier *[5]string)  {
	set.content[*specifier]=dumb
}

func (set *SpecifierSet)Del(specifier *[5]string)  {
	delete(set.content,*specifier)
}
func NewSpecifierSet() *SpecifierSet{
	return &SpecifierSet{content: make(map[[5]string]void)}
}

func CopyFloatSlice(src []float64) (dst []float64)  {
	dst=make([]float64,len(src))
	for idx,v:=range src{
		dst[idx]=v
	}
	return dst
}

func CopyMap(m map[string][]float64) (dst map[string][]float64)  {
	dst=make(map[string][]float64)
	for k,v:=range m{
		dst[k]= CopyFloatSlice(v)
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


func ShuffleStrings(strs []string){
	rand.Shuffle(len(strs), func(i, j int) {
		strs[i],strs[j]=strs[j],strs[i]
	})
}

func CopyInt64Slice(src []int64)(dst []int64)  {
	for _,v:=range src{
		dst=append(dst,v)
	}
	return
}


func ShuffleFloats(fs []float64)  {
	rand.Shuffle(len(fs), func(i, j int) {
		fs[i],fs[j]=fs[j],fs[i]
	})
}
func ShuffleInts(ints []int)  {
	rand.Shuffle(len(ints), func(i, j int) {
		ints[i],ints[j]=ints[j],ints[i]
	})
}

//todo correctness check
func Copy(dst []byte,dstStart int,src []byte,srcStart,n int){
	for i:=0;i<n;i++{
		dst[dstStart+i]=src[srcStart+i]
	}
}

func Filter(dst,src []interface{},pred func(e interface{}) bool)  {
	for _,i:=range src{
		if pred(i){
			dst=append(dst,i)
		}
	}
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

