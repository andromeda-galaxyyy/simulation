import json
import time
import copy
import socket
import sys
import  copy
from utils.log_utils import debug, info, err
class table:
    def __init__(self,links,path,switches,monitor,vlan):
        self.Links=copy.deepcopy(links)
        self.link_flag=dict()  ### 记录待测链路是否进行了多播返回操作
        self.n_switches=switches
        self.monitor=monitor
        self.sip="10.0.0.1"
        self.dip="10.0.0.2"
        self.multi_flag={}
        self.paths=path
        self.multi_p=[]
        self.multi_n={}
        self.json_dict={}
        self.vlan_id=vlan
        # self.act={"action 1":{},"action 2":{}}
    ################################################
    # 多播的交换机id,以及多播下一跳
    def compute_muiti(self,l):
        multi_nodes={}
        multi_list=[]
        # x=0
        for i in range(len(l)):## 对于每一条path来说
            for j in range(i+1,len(l)):   ###对于其他路径来说
                for n in range(min(len(l[i]),len(l[j]))):    #获得两条路径的最短长度
                    if l[i][n]==l[j][n]:
                        continue
                    if l[i][:n] not in multi_list:
                        multi_list.append(l[i][:n])
                        x = len(multi_list)
                        multi_nodes[x] = []
                        multi_nodes[x].append(l[i][n])
                        multi_nodes[x].append(l[j][n])
                    else:
                        index = multi_list.index(l[i][:n]) + 1
                        if l[i][n] not in multi_nodes[index]:
                            # print(l[i][:n], "already in multi_p", "add:", l[i][n])
                            multi_nodes[index].append(l[i][n])
                        elif l[j][n] not in multi_nodes[index]:
                            # print(l[i][:n], "already in multi_p", "add:", l[j][n])
                            multi_nodes[index].append(l[j][n])
                    break
        return multi_list,multi_nodes
    #############################################
    #结果汇总
    def make_res(self):
        self.multi_p, self.multi_n = self.compute_muiti(self.paths)
        self.is_probelink()
        print("multi_p", self.multi_p, '\n', "multi_n", self.multi_n)
        self.IPV4forward()
        self.last_forward()
        self.multi_forward()
        info(self.json_dict)
        info(len(self.json_dict['23']))
        with open('commmands.json','w') as f:
            data=json.dumps(self.json_dict)
            # try:
            #     s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            #     s.connect(("localhost",6666))
            # except socket.error as msg:
            #     print(msg)
            #     sys.exit(1)
            # # print(len(data))
            # data_b=str.encode(data)
            # data_b+="*"
            # s.sendall(data_b)
            json.dump(self.json_dict,f)
            # json.dump(self.edges_port,f)
        return self.json_dict
    ###########################################
    #判断是否是待测链路    探测链路两端节点都要返回数据包（只处理了一端节点 另一端节点未处理#）
    # def probeLink(self):
    #     for i in self.Links:
    def is_probelink(self):
        links=self.Links
        for x in links:
            self.link_flag[x]=0
        for path in self.paths:
            p_list = []
            for i in range(len(path)-1):##判断待测链路节点是否已经是多播节点 不是则新建多播组 是则加入多播组,尾节点会直接返回
                flag=0
                p_list.append(path[i])

                if (path[i],path[i+1]) in self.Links:
                    #print(self.Links)
                    # print(self.Links)
                    # print(path[i], path[i + 1],11111)
                    # print(self.link_flag)
                    flag=1
                elif (path[i+1],path[i]) in self.Links:
                    #print(path[i+1], path[i],22222222)
                    flag=2
                if flag == 1 and self.link_flag[(path[i],path[i+1])]==0:
                        ##处理节点1
                        self.add_multi(p_list,path,i)
                        ##处理节点2
                        if path[i+1]==path[-1]:  #如果尾节点是路径最后一跳 则不进行尾节点的操作
                            continue
                        p_next_list = copy.deepcopy(p_list)
                        p_next_list.append(path[i + 1])
                        self.add_multi(p_next_list,path,i+1)
                        # p_list.pop()
                        self.link_flag[(path[i], path[i + 1])] =1
                elif flag==2 and self.link_flag[(path[i+1],path[i])]==0:
                    # print("flag==2")
                    # p_list.append(path[i])
                    self.add_multi(p_list, path, i)
                    ##处理节点2
                    if path[i + 1] == path[-1]:  # 如果尾节点是路径最后一跳 则不进行尾节点的操作
                        continue
                    p_next_list=copy.deepcopy(p_list)
                    p_next_list.append(path[i + 1])
                    # time.sleep(1)
                    self.add_multi(p_next_list, path, i + 1)
                    # p_list.pop()
                    self.link_flag[(path[i+1], path[i])] = 1


    def add_multi(self,p_list,path,i):      #####path[i] 不仅返回给上一跳 还要发送到下一跳
        if p_list in self.multi_p:
            index_p = self.multi_p.index(p_list) + 1
            if path[i+1] not in self.multi_n[index_p]:
                self.multi_n[index_p].append(path[i+1])
                # print(p_list, "is in multi_p,在{}处添加多播节点i+1=>{}".format(index_p,path[i+1]))
            if path[i-1] not in self.multi_n[index_p]:
                self.multi_n[index_p].append(path[i-1])
                # print(p_list, "is in multi_p,在{}处添加多播节点i-1=>{}".format(index_p, path[i - 1]))
        else:
            self.multi_p.append(p_list)
            n_list = [path[i-1], path[i+1]]
            self.multi_n[len(self.multi_p)] = n_list
            # print(p_list, "is not in multi_p,添加多播节点=>{}".format(n_list),"multi_p 长度：",len(self.multi_p))
            # print(self.multi_p)

    ###########################################
    #中间转发节点
    def IPV4forward(self):
        for path in self.paths:
            # print("path ",path)
            p_list=[0]
            last_node = path[-1]
            for i in range(1,len(path)-1):
                # print("i:",i)
                multi_flag=1
                p_list.append(path[i])
                if p_list in self.multi_p:
                    n_index=self.multi_p.index(p_list)+1
                    if path[i+1] not in self.multi_n[n_index]:
                        multi_flag=0
                elif p_list not in self.multi_p:
                    multi_flag=0
                if multi_flag ==0:
                    # print((path[i],path[i+1]),'=>',self.get_port(path[i], path[i+1]))
                    temp = {}
                    outport=[]
                    outport.append(path[i+1])
                    temp['outport'] = outport
                    act={}
                    act['action1']=temp
                    # act['action 2']={}
                    table = {}
                    table['10.0.0.1,{}'.format(path[i-1])] = act
                    if '{}'.format(path[i]) not in self.json_dict.keys():
                        self.json_dict['{}'.format(path[i])] = table
                    elif '10.0.0.1,{}'.format(path[i-1]) in self.json_dict['{}'.format(path[i])].keys():
                        self.json_dict['{}'.format(path[i])][
                            '10.0.0.1,{}'.format(path[i-1])]['action1']['outport'] = outport
                    elif '10.0.0.1,{}'.format(path[i-1]) not in self.json_dict['{}'.format(path[i])].keys():
                        self.json_dict['{}'.format(path[i])]['10.0.0.1,{}'.format(path[i-1])]=act

                #返回数据包的处理
                # if path[i]!=last_node:  #中间节点的返回处理       (src,inport)  action1: outport:
                outport = []
                outport.append(path[i - 1])
                for j in range(i+1,len(path)):
                    temp={}
                    act={}
                    temp['outport'] = outport
                    act['action1']=temp
                    # self.act['action 2']={}
                    table = {}
                    table['10.0.1.{},{}'.format(path[j], path[i+1])] = act
                    if '{}'.format(path[i]) not in self.json_dict.keys():
                        # print('{}'.format(path[i]),"not in elf.json_dict.keys()","self.json_dict['{}'] ={}".format(path[i],table))
                        self.json_dict['{}'.format(path[i])] = table
                    elif '10.0.1.{},{}'.format(path[j],path[i+1]) in self.json_dict['{}'.format(path[i])].keys():
                        # print('{}'.format(path[i]),('10.0.1.{},{}'.format(path[j],self.get_port(path[i], path[i+1]))),"in json list","['action1']['outport'] = ",self.get_port(path[i], path[i-1]))
                        self.json_dict['{}'.format(path[i])][
                            '10.0.1.{},{}'.format(path[j], path[i + 1])]['action1']['outport'] = outport
                    elif ('10.0.1.{}'.format(path[j]), path[i+1]) not in self.json_dict['{}'.format(path[i])].keys():
                        # print('{}'.format(path[i]),('10.0.1.{}'.format(path[j]), self.get_port(path[i], path[i + 1])), "not in json list",
                        #       '10.0.1.{},{}'.format(path[j], self.get_port(path[i], path[i + 1])),"=",act)
                        self.json_dict['{}'.format(path[i])]['10.0.1.{},{}'.format(path[j], path[i+1])]=act



    ###########################################
    #路径最后一跳 返回探测包  修改srcip 、 dstip
    def last_forward(self):
        for path in self.paths:
            ####json
            temp={}
            # temp['outport']=self.get_port(path[- 1],path[- 2])
            temp['src']='10.0.1.{}'.format(path[-1])
            temp['dst']='10.0.0.1'
            temp["vlan"]=self.vlan_id[(path[-1],path[-2])]
            # temp['vlan']=self.get_port(path[- 1],path[- 2])
            act={}
            act['action2']=temp
            table={}
            table['10.0.0.1,{}'.format(path[- 2])]=act
            if '{}'.format(path[-1]) not in self.json_dict.keys():
                self.json_dict['{}'.format(path[-1])] = table
            elif '10.0.0.1,{}'.format(path[- 2]) in self.json_dict[
                '{}'.format(path[-1])].keys():
                self.json_dict['{}'.format(path[-1])][
                    '10.0.0.1,{}'.format( path[- 2])]['action2']=temp
            elif '10.0.0.1,{}'.format(path[- 2]) not in self.json_dict[
                '{}'.format(path[-1])].keys():
                self.json_dict['{}'.format(path[-1])][
                    '10.0.0.1,{}'.format(path[- 2])] = act
    ###########################################
    #####处理多播转发 多播组与端口的绑定以及多播后srcip、dstip的修改
    def multi_forward(self):
        for i in self.multi_n.keys():
            # egress_rid=0
            n_list=self.multi_p[i-1]
            # print("n_list:",n_list,"multi_n:",self.multi_n[i])
            outport=[]
            for m in self.multi_n[i]:
                if m!=n_list[-2]:
                    # print(n_list[-1],"=>",m,"outport:",self.get_port(n_list[-1], m))
                    outport.append(m)
                else:
                    # print(n_list,"=>",m,"修改src、dst","outport=",self.get_port(n_list[-1],n_list[-2]))
                    temp = {}
                    # temp['outport'] = self.get_port(n_list[-1],n_list[-2])
                    temp['src'] = '10.0.1.{}'.format(n_list[-1])
                    temp['dst'] = '10.0.0.1'
                    temp['vlan'] = self.vlan_id[(n_list[-1],n_list[-2])]
                    # temp['vlan'] = self.get_port(n_list[-1],n_list[-2])
                    act = {}
                    act['action2'] = temp
                    table = {}
                    table['10.0.0.1,{}'.format(n_list[-2])] = act
                    if '{}'.format(n_list[-1]) not in self.json_dict.keys():
                        self.json_dict['{}'.format(n_list[-1])] = table
                    elif '10.0.0.1,{}'.format(n_list[-2]) in self.json_dict[
                        '{}'.format(n_list[-1])].keys():
                        self.json_dict['{}'.format(n_list[-1])][
                            '10.0.0.1,{}'.format(n_list[-2])]['action2'] = temp
                    elif '10.0.0.1,{}'.format(n_list[-2]) not in self.json_dict[
                        '{}'.format(n_list[-1])].keys():
                        self.json_dict['{}'.format(n_list[-1])][
                            '10.0.0.1,{}'.format(n_list[-2])] =act
            # print("outport:",outport)
            temp = {}
            temp['outport'] = outport
            act = {}
            act['action1'] = temp
            table = {}
            table['10.0.0.1,{}'.format(n_list[-2])] = act
            if '{}'.format(n_list[-1]) not in self.json_dict.keys():
                self.json_dict['{}'.format(n_list[-1])] = table
            elif '10.0.0.1,{}'.format(n_list[-2]) in self.json_dict[
                '{}'.format(n_list[-1])].keys():
                self.json_dict['{}'.format(n_list[-1])][
                    '10.0.0.1,{}'.format(n_list[-2])]['action1'] = temp
            elif '10.0.0.1,{}'.format(n_list[-2]) not in self.json_dict[
                '{}'.format(n_list[-1])].keys():
                self.json_dict['{}'.format(n_list[-1])][
                    '10.0.0.1,{}'.format( n_list[-2])] = act

if __name__ == '__main__':
    # links=[(2,3),(1,6),(3,4)]
    # paths=[[0,5, 2, 1], [0,5, 6, 1], [0,5, 2, 3], [0,5, 3, 4], [0,5, 7, 4], [0,5, 6, 7]]
    # paths=[[23, 12, 13, 14, 15],[23, 12, 22],[23, 24, 13, 14, 15, 16]]
    # links=[(23,12),(16,15),(14,15)]
    # # print(len(paths))
    print("done!")
