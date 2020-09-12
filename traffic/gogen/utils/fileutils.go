package utils

import (
	"bufio"
	"os"
)

func FileExist(fn string) bool  {
	info,err:=os.Stat(fn)
	if os.IsNotExist(err){
		return false
	}
	return !info.IsDir()
}

func IsFile(fn string) bool  {
	return FileExist(fn)
}

func DirExists(dirname string) bool{
	info,err:=os.Stat(dirname)
	if os.IsNotExist(err){
		return false
	}
	return info.IsDir()
}

func IsDir(dirname string) bool  {
	return DirExists(dirname)
}

func ReadLines(fpath string) (res []string,err error) {
	file,err:=os.Open(fpath)
	if err!=nil{
		return nil,err
	}
	defer file.Close()
	scanner:=bufio.NewScanner(file)
	for scanner.Scan(){
		res=append(res,scanner.Text())
	}
	return res,scanner.Err()
}

func RMDir(dir string) error {
	return os.RemoveAll(dir)
}

func CreateDir(dir string) error {
	return os.Mkdir(dir,os.ModePerm)
}



