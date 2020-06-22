# Rule
Roadmap

模块化
每个模块使用dumb，先把系统运行起来，再说
socket+json,所有的编码均为ASCII编码

每个模块下面给出了输入例子（如果有）

# classify
这个模块用于判断属于哪种流
接受统计量，示例为receive.demo.json,端口为1025

返回结果  示例为resp.demo.json "0"代表视频流，"1"为iot流，"2"为voip流
统计包大小包间隔，
包间隔为nanosecond
包大小为byte


# deploy
存放系统启动脚本、编译脚本等
目前放的是ditg编译脚本，系统运行前首先要编译ditg

# traffic
这个模块主要用于主机生成流量

主机会上报流的统计信息，socket.demo.json
specifier 字段为五元祖，均为字符串，顺序为src_port，dst_port,src_ip,dst_ip,protocol,
stats为统计信息，均为float，顺序如示例

控制器端口为1026,需要在1026这个端口有一个socket程序在监听

# topo
这个模块主要用于建立topo，目前是mininet，仅支持python2，因为python版本的原因，这个模块相对独立，不依赖于任何外部模块，外部模块使用python3
考虑到网络中需要存在两种流，大带宽流和低延迟流，所以每个交换机上挂载k个主机，分别产生大带宽流和低延迟流，因此我们约定如下：
如果交换机的ID为N（从0开始），那么挂载的k个主机 id分别为k*N+0,k*N+1,k*N+2,....k*N+k-1
如果主机id为奇数，那么产生大流量，如果主机id为偶数，产生低延迟流量
他们的ip地址由下面的函数产生

```python
def generate_ip(id):
	id = int(id)+1
	if 1 <= id <= 254:
		return "10.0.0." + str(id)
	if 255 <= id <= 255 * 254+253:
		return "10.0." + str(id // 254) + "." + str(id % 254)
	raise Exception("Cannot support id address given a too large id")
```

比如id=0---> '10.0.0.1'
id=255--->'10.0.1.1'
id=253--->'10.0.0.254'

他们的mac地址由下面的函数产生
```python
def generate_mac(id):
	id = int(id) + 1	
    # convert to base 16 str
	raw_str=base_16(id)
	if len(raw_str)>12:
		raise Exception("Invalid id")
	#reverse
	raw_str=raw_str[::-1]
	to_complete=12-len(raw_str)
	while to_complete>0:
		raw_str+="0"
		to_complete-=1
	mac_addr=":".join([raw_str[i:i + 2] for i in range(0, len(raw_str), 2)])
	mac_addr=mac_addr[::-1]
	return mac_addr
```
比如id=1 --->'00:00:00:00:00:02'
id=257---> '00:00:00:00:01:02'

## 关于分布式ovs
原理是同一台worker上的ovs通信使用veth，不同worker上的ovs通信使用gre隧道
关于qos设置，延迟，带宽，丢包率等，使用tc工具

ovs上挂载的主机采用namespace技术进行虚拟化，理论上可以运行任何程序

关于nat，ovs上的主机需要与外界通信，比如控制器，需要使用nat，nat的原理比较繁琐。

每个主机上额外有一个网卡，不同的子网10.1.0.0/24，该网卡用于nat，并且已经配置了默认路由,该网卡通过veth接到一台隐藏的ovs上
该ovs的名称为nat，该ovs对控制器透明，实际上，所有的nat功能都对控制器透明

关于ovs拓扑切换问题，


## 关于流量产生和监听
使用gen和golisten，如果需要编译，需要配置golang环境，然后运行gogen文件夹下面的build.sh

# routing
这个模块主要用于决策路由,交互见json，
routing模块的socket端口为1027
默认路由的模块socket端口为1028

考虑到topo需要切换，那么控制器应该在1029端口，设置一个socket服务器，具体流程如下

data plane===1====>controller<====请求/返回默认路由===>算法1028



# 运行测试
##  编译ditg
运行deploy/ditg.sh 编译ditg
## Mininet Topo
目前可以自定义
例子是topo/files/topo.json中给出的，三个节点，ABC，B---A---C,目前没有自定义链路QoS
如需自定义topo，修改topo.json
为邻接矩阵，矩阵中的每个元素代表一条链路，链路QoS为带宽、延迟、丢包率、切换代价、以后的格式也这样
元素中如果出现-1,表示这条链路不通
邻接矩阵，仅表示半边，比如A----B，仅表示A--->B的连接
 
运行例子需要ryu controller，默认ip地址为localhost,监听默认端口，并且controller用于接受主机上报的socket端口为1026

## test 
文件夹test下面存放测试代码，目前主要测试socket通信




# 总结
