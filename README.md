# Rule
Roadmap

模块化
每个模块使用dumb，先把系统运行起来，再说
socket+json,所有的编码均为ASCII编码

每个模块下面给出了输入例子（如果有）

# classify
这个模块用于判断属于哪种流
接受统计量，示例为receive.demo.json,端口为1025

返回结果  示例为resp.demo.json "0"代表大流量，"1"低时延


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
考虑到网络中需要存在两种流，大带宽流和低延迟流，所以每个交换机上挂载两个主机，分别产生大带宽流和低延迟流，因此我们约定如下：
如果交换机的ID为N（从0开始），那么挂载的两个主机 id分别为2*N 2*N+1
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

比如id=1---> '10.0.0.1'
id=255--->'10.0.1.1'
id=254--->'10.0.0.254'

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



## 关于流量产生
工具为DITG，但是有bug，目前的patch是使用脚本，进程crash之后重新运行
ITGManager ips_file lambda duration controller_ip port

### DITG工作原理
DITG可以自定义流量特性，自定义包间隔、包长度，这两个量分别由两个文件控制idt、ps文件，这两个文件是由python分析pcap文件产生的
DITG有潜在的问题，比如流的时间无法精确控制，例如（流的时间如果是10s，那么DITG运行时间可能超过10s）
对源码进行了一些修改 放在traffic/ditg/下面

[ DITG手册 ](http://www.grid.unina.it/software/ITG/manual/)

DITG支持Daemon模式，项目采用ITGManager生成Possion到达的流，流根据idt和ps文件产生

# routing
这个模块主要用于决策路由,交互见json，
routing模块的socket端口为1027



# 运行测试
##  编译ditg
运行deploy/ditg.sh 编译ditg
## Mininet Topo
目前可以自定义
例子是topo/files/topo.json中给出的，三个节点，ABC，B---A---C,目前没有自定义链路QoS
如需自定义topo，修改topo.json
为邻接矩阵，矩阵中的每个元素代表一条链路，链路QoS为带宽、延迟、丢包率，以后的格式也这样
 
运行例子需要ryu controller，默认ip地址为localhost,监听默认端口，并且controller用于接受主机上报的socket端口为10000

## test 
文件夹test下面存放测试代码，目前主要测试socket通信



