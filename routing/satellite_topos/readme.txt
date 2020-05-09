#因为真实的卫星轨道参数数据还没有给
#所以这里得到的数据是仿照铱星系统假设的参数运行得到的
#六个轨道，每个轨道11颗卫星，共66颗卫星



# 读取拓扑列表，总共44个拓扑，
# 每个拓扑都存储在一个66*66的矩阵中
# 数值为0代表该边不存在，
# 数值为None代表该边此时关闭，
# 数值为正数代表该边开启，数值即为延时

import pickle
# delaygraph_py2_v2.txt 是python2版本
# delaygraph_py3_v2.txt 是python3版本


with open('delaygraph_py2_v2.txt','rb') as f:
    graphList = pickle.load(f)




# 读取时间点列表，总共44个时间点
# 代表拓扑开始的时间点
# 一个时间点对应一个拓扑开始的时间  单位为s/秒
# timelist_py2.txt 对应python2
# timelist_py3.txt 对应python3
# 一整个大周期约为6035s，拓扑变化时间为157.95s、116.36s交替

with open('timelist_py2.txt','rb') as f:
    timeList = pickle.load(f)
