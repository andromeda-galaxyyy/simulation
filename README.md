### simulation 

采用Python3.6编写

##### deploy 

用于相关程序的部署，包括：

1. 流量分类负载均衡
2. docker服务
3. 相关演示程序脚本入口
4. 代码同步脚本
5. 相关环境变量设置脚本



##### static 

配置文件和拓扑文件



##### telemetry 

网络状态探测模块



##### test 

部分功能unit测试程序



##### classify

流量分类模块，包括

1. pcap解析程序，将pcap解析为packet size文件和interval departure time文件
2.  模型训练程序
3. 模型封装程序(server端)
4. 请求响应示例



##### topo

拓扑搭建模块，包括：

1. 控制台程序main.py
2. 流量模式变换
3. 拓扑变换
4. router（分布式服务端）



##### traffic 

流量生成和解析相关程序，代码结构下面有详细的，这里只是简单保存编译后的二进制程序



##### routing

路由优化模块，包括：

1. online算法
2. 最短路算法
3. ilp算法
4. 机器学习算法
5. 各种算法server端封装



##### utils

各种工具方法的封装



##### common 

一些公共数据结构和常量



### Traffic 

采用Go编写

##### api

网络状态指标API服务端，基于gin



##### models 

公共数据结构



##### bin

编译好的二进制程序，包括Linux和Windows环境，其中Linux应该能够直接运行



##### collector

模块化的程序，main函数给出了使用示例，可以比较方便地实现接口，进行程序扩展（参考handler和registry的实现方式）

日志收集程序，主要包括：

1. 注册中心
2. 文件系统监控
3. handler



##### utils 

部分工具函数，包括：

1. 位操作
2. Redis连接 
3. 文件系统
4. Socket 连接
5. 时间
6. 容器



##### gen 

流量注入程序



##### golisten

QoS分析程序，支持全部流量和部分流量分析





