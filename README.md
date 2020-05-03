#Rule

Roadmap

模块化
每个模块使用dumb，先把系统运行起来，再说

# 所有的编码均为ASCII编码
# classify
这个模块用于判断属于哪种流
接受统计量，示例为receive.demo.json

返回结果  示例为resp.demo.json "0"代表大流量，"1"低时延


#traffic
这个模块主要用于主机生成流量

主机会上报流的统计信息，socket.demo.json
specifier 字段为五元祖，均为字符串，顺序为src_port，dst_port,src_ip,dst_ip,protocol,
stats为统计信息，均为float，顺序如示例

## 关于流量产生
工具为DITG，但是有bug，目前的patch是使用脚本，进程crash之后重新运行
ITGManager ips_file lambda duration controller_ip port

#routing
这个模块主要用于决策路由


## 测试
各自搭建的拓扑为田字格，九个交换机，交换机编号从0-8，从上到下，从左往右
每个交换机挂载了一个主机，ip从10.0.0.1到10.0.0.9/24





