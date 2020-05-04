//
// Created by Stack on 5/4/20.
//

#include "socket_util.h"
#define MAX(a,b) a>b?a:b
#define MIN(a,b) a<b?a:b

using json=nlohmann::json;
using string=std::string;
using stats=std::vector<double>;

class StatsGenerator{
public:
    virtual stats operator()(string& idt_fn,string& ps_fn)=0;
};

class RandomStatsGen: public StatsGenerator{
    double upper=0;
    double lower=0;
    int dim=8;
    std::uniform_real_distribution<double> double_uni_dist;
    static std::default_random_engine engine;
public:
    explicit RandomStatsGen(double u=10, double l=20,int d=8): upper(u), lower(l),dim(d){
        double_uni_dist=std::uniform_real_distribution<double>(lower,upper);

    }
    stats operator()(string& idt_fn,string& ps_fn) override;
};
std:: default_random_engine RandomStatsGen::engine=std::default_random_engine();

stats RandomStatsGen::operator()(string &idt_fn, string &ps_fn) {
    stats res(8);
    for(int i=0;i<dim;i++){
        res[i]=double_uni_dist(engine);
    }
    return res;
}


class WindowStatsGenerator: public StatsGenerator{
    int win_size=50;
    stats do_calculate(stats& idts,stats& pss,stats& res);
    static double mean(stats& nums);
    static double stdvar(stats& nums, double m);
    static std::pair<double,double> min_and_max(stats& nums);
public:
    explicit WindowStatsGenerator(int size=50): win_size(size){

    }
    stats operator()(string& idt_fn,string& ps_fn) override;

};

stats WindowStatsGenerator::operator()(string &idt_fn, string &ps_fn) {
    stats res;
    //inter departure time
    stats idts;
    //inter packet size
    stats pss;
    std::ifstream infile(idt_fn);
    string line;
    int k=win_size;
    //read inter departure time
    while(k){
        k--;
        if(std::getline(infile,line)){
            if(line.empty()) break;
            idts.push_back(std::stod(line));
        }
    }
    //read packet size
    k=win_size;
    infile.close();
    std::ifstream ps_file(ps_fn);
    while(k){
        k--;
        if(std::getline(ps_file,line)){
            if(line.empty()) break;
            pss.push_back(std::stod(line));
        }
    }
    do_calculate(idts,pss,res);
    return res;
}

stats WindowStatsGenerator::do_calculate(stats &idts, stats &pss,stats& res) {
    std::pair<double,double> min_max=min_and_max(idts);
    res.push_back(min_max.first);
    res.push_back(min_max.second);
    double m=mean(idts);
    res.push_back(m);
    res.push_back(stdvar(idts,m));

    min_max=min_and_max(pss);
    res.push_back(min_max.first);
    res.push_back(min_max.second);
    m=mean(pss);
    res.push_back(m);
    res.push_back(stdvar(pss,m));

    return res;
}

double WindowStatsGenerator::mean(stats &nums) {
    double sum=std::accumulate(nums.begin(),nums.end(),0.0);
    return sum/nums.size();
}

double WindowStatsGenerator::stdvar(stats &nums, double m) {
    std::vector<double> diff(nums.size());
    std::transform(nums.begin(), nums.end(), diff.begin(),
                   std::bind2nd(std::minus<double>(), m));
    double sq_sum = std::inner_product(diff.begin(), diff.end(), diff.begin(), 0.0);
    double stdev = std::sqrt(sq_sum / nums.size());
    return stdev;
}

std::pair<double, double> WindowStatsGenerator::min_and_max(stats &nums) {
    std::pair<double,double> res;
    for(auto d:nums){
        res.first=MIN(res.first,d);
        res.second=MAX(res.second,d);
    }
    return res;
}

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
        std::cout<<"ITGManager 2 Error:"<<std::endl;
        std::cout<<"Usage: ITGManager lambda ditg_dir"<<std::endl;
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

    //read possion lamba
    lambda=strtol(argv[3],nullptr,10);
    controller_ip=string(argv[4]);
    controller_socket_port=strtol(argv[5],nullptr,10);



    json statistics;
    string statistic_fn=ditg_dir+"/statistics.json";
    std::ifstream json_stream(statistic_fn);
    json_stream>>statistics;
    int num_flows=statistics["count"].get<int>();
    std::cout<<"num flows "<<num_flows<<std::endl;

    std::default_random_engine engine;
    std::exponential_distribution<double> inter_flow_distr(lambda);
    std::uniform_int_distribution<int> port_uniform_distribution(1500, 65534);
    std::uniform_int_distribution<int> remote_ip_uniform_distribution(0, addrs.size() - 1);
    std::uniform_real_distribution<double> float_uniform_distribution(10, 20);
    std::uniform_int_distribution<int> flow_uni_distribution(0,num_flows-1);
    double wait=0;
    json report;
    WindowStatsGenerator statsGenerator(25);
    while(1){
        //pick a flow
        params="";
        auto flow=statistics["flows"].at(flow_uni_distribution(engine));
        wait=inter_flow_distr(engine);
        //TODO avoid existing port
        int lp=port_uniform_distribution(engine);
        int rp=port_uniform_distribution(engine);
        string remote_ip=addrs[remote_ip_uniform_distribution(engine)];
        specifier[0]=std::to_string(lp);
        specifier[1]=std::to_string(rp);
        specifier[2]=self_ip;
        specifier[3]=remote_ip;
        specifier[4]=flow["proto"].get<string>();
        report["specifier"]=specifier;

        string idt_fn=ditg_dir+flow["idt"].get<string>();
        string ps_fn=ditg_dir+flow["ps"].get<string>();
        std::cout<<idt_fn<<std::endl;
        //
        stats stats_to_report=statsGenerator(idt_fn,ps_fn);
        report["stats"]=stats_to_report;
        std::cout<<report.dump()<<std::endl;

        break;

    }

}
