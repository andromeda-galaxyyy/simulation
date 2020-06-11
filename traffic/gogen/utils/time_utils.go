package utils

import (
	"fmt"
	"time"
)

func NowInMilli() int64  {
	return int64(int(time.Now().UnixNano() / 1e6))
}

func NowInNano()int64  {
	return time.Now().UnixNano()
}

func NowInString()string  {
	t:=time.Now()
	return fmt.Sprintf("%d",t.UnixNano())
}
