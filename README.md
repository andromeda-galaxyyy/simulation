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
###  编译ditg
运行deploy/ditg.sh 编译ditg
### Mininet Topo
目前可以自定义
例子是topo/files/topo.json中给出的，三个节点，ABC，B---A---C,目前没有自定义链路QoS
如需自定义topo，修改topo.json
为邻接矩阵，矩阵中的每个元素代表一条链路，链路QoS为带宽、延迟、丢包率，以后的格式也这样
 
运行例子需要ryu controller，默认ip地址为localhost,监听默认端口，并且controller用于接受主机上报的socket端口为10000





