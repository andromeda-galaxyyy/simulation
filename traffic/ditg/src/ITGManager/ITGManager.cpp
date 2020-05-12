//
// Created by Stack on 5/4/20.
//

#include "common.h"
#include "stats.h"

#define MODULE_NAME "ITGManager"

string params;
string ditg_dir="/tmp/ditgs/";
int lambda=5;
string ips_fn;
string controller_ip;
int controller_socket_port;
string specifier[5];



//ips_fn 1
//ditg_dir 2
//lambda 3
//controller ip 4
//controller socket_port 5
int main(int argc,char* argv[]){
    argc--;
    if(argc<5){
        print_error(MODULE_NAME,"Invalid arguments");
        print_msg(MODULE_NAME,"Usage: ITGManager ips_fn ditg_dir lambda controller_ip controller_socket_port");
        exit(-1);
    }
    ips_fn=string(argv[1]);
    ip_addrs addrs;
    string self_ip;
    read_ip_files(ips_fn,self_ip,addrs);

    ditg_dir=string(argv[2]);
    if(ditg_dir[ditg_dir.size()-1]!='/'){
        ditg_dir.append("/");
    }
    if(!dir_exists(ditg_dir)){
        print_error(MODULE_NAME,"DITG Dir not exists! ",ditg_dir.c_str());
        exit(-1);
    }

    //read possion lamba
    lambda=strtol(argv[3],nullptr,10);

    controller_ip=string(argv[4]);
    controller_socket_port=strtol(argv[5],nullptr,10);



    json statistics;
    string statistic_fn=ditg_dir+"/statistics.json";
    if(!file_exists(statistic_fn)){
        print_error(MODULE_NAME,"Cannot find file: statistics.json");
        exit(-1);
    }
    std::ifstream json_stream(statistic_fn);
    json_stream>>statistics;
    int num_flows=statistics["count"].get<int>();

    std::default_random_engine engine;
    std::exponential_distribution<double> inter_flow_distr(lambda);
    std::uniform_int_distribution<int> port_uniform_distribution(1500, 65534);
    std::uniform_int_distribution<int> remote_ip_uniform_distribution(0, addrs.size() - 1);
    std::uniform_real_distribution<double> float_uniform_distribution(10, 20);
    std::uniform_int_distribution<int> flow_uni_distribution(0,num_flows-1);
    double wait=0;
    json report;
    WindowStatsGenerator statsGenerator(25);
    std::default_random_engine generator;
    while(1){
        //pick a flow
        params="";
        auto flow=statistics["flows"].at(flow_uni_distribution(engine));
        wait=inter_flow_distr(engine);
        //TODO avoid existing port
        int lp=port_uniform_distribution(engine);
        int rp=port_uniform_distribution(engine);
        string remote_ip=addrs[remote_ip_uniform_distribution(engine)];
        // fill in specifier
        //local_ip remote ip self_ip remote_ip proto
        specifier[0]=std::to_string(lp);
        specifier[1]=std::to_string(rp);
        specifier[2]=self_ip;
        specifier[3]=remote_ip;
        specifier[4]=flow["proto"].get<string>();

        report["specifier"]=specifier;

        string idt_fn=ditg_dir+flow["idt"].get<string>();
        string ps_fn=ditg_dir+flow["ps"].get<string>();

        if(!file_exists(idt_fn)){
            print_error(MODULE_NAME,"Cannot find idt file:",idt_fn.c_str());
            exit(-1);
        }

        stats stats_to_report=statsGenerator(idt_fn,ps_fn);
        report["stats"]=stats_to_report;
        std::cout<<report.dump()<<std::endl;

        append_params(params,"-a",specifier[3]);
        append_params(params,"-rp",specifier[1]);
        append_params(params,"-sp",specifier[0]);
        append_params(params,"-T",specifier[4]);

        append_params(params,"-Ft",idt_fn);
        append_params(params,"-Fs",ps_fn);



        int res=DITGsend("localhost", const_cast<char* >(params.c_str()));
        if(res==-1){
            print_error(MODULE_NAME,"Cannot perform ITGSend\n");
        }else{
            if(!report_to_controller(controller_ip.c_str(),controller_socket_port,report)){
                print_error(MODULE_NAME,"Cannot send msg to controller");
            }
        }

        long long in_milli =(long long)(inter_flow_distr(generator)*1000);
        SLEEP_MILLI(in_milli);
    }

}
