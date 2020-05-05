//
// Created by Stack on 5/5/20.
//

#include "common.h"

#include "stats.h"

#define MAX(a,b) a>b?a:b
#define MIN(a,b) a<b?a:b

std::default_random_engine RandomStatsGen::engine;

void RandomStatsGen::set_engine(int seed) {
   RandomStatsGen::engine=std::default_random_engine(seed);
}

RandomStatsGen::RandomStatsGen(double l,double u,int d):lower(l),upper(u),dim(d){
    double_uni_dist=std::uniform_real_distribution<double>(lower,upper);
}


stats RandomStatsGen::operator()(string &idt_fn, string &ps_fn) {
    stats res(8);
    for(int i=0;i<dim;i++){
        res[i]=double_uni_dist(RandomStatsGen::engine);
    }
    return res;
}



WindowStatsGenerator::WindowStatsGenerator(int ws):win_size(ws){}

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
        line="";
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
        line="";
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
    std::pair<double,double> res={1e10,-1};
    for(auto d:nums){
        res.first=MIN(res.first,d);
        res.second=MAX(res.second,d);
    }
    return res;
}