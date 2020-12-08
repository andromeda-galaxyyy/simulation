package main

import "encoding/json"

type result struct {
	Ts         int64  `json:"ts"`
	Fn         string `json:"fn"`
	FlowId     int64  `json:"flow_id"`
	Label      string `json:"label"`
	Prediction string `json:"prediction"`
	IsValid    bool   `json:"is_valid"`
}

func (r *result) box()([]byte,error){
	return json.Marshal(*r)
}

func (r *result)unbox(data []byte) error{
	return json.Unmarshal(data,r)
}


