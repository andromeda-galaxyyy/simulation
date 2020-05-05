//
// Created by Stack on 5/5/20.
//

#include "common.h"
#ifndef SRC_STATS_H
using stats=std::vector<double>;

class StatsGenerator{
public:
    virtual stats operator()(string& idt_fn,string& ps_fn)=0;
};

class RandomStatsGen: public StatsGenerator{
    double upper;
    double lower;
    int dim;
    std::uniform_real_distribution<double> double_uni_dist;
    static std::default_random_engine engine;
public:
    explicit RandomStatsGen(double l=10, double u=20,int d=8);
    stats operator()(string& idt_fn,string& ps_fn) override;
    static void set_engine(int seed=40);
};



class WindowStatsGenerator: public StatsGenerator{
    int win_size=50;
    stats do_calculate(stats& idts,stats& pss,stats& res);
    static double mean(stats& nums);
    static double stdvar(stats& nums, double m);
    static std::pair<double,double> min_and_max(stats& nums);
public:
    explicit WindowStatsGenerator(int size=50);
    stats operator()(string& idt_fn,string& ps_fn) override;
};


#define SRC_STATS_H

#endif //SRC_STATS_H
