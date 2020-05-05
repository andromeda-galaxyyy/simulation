//
// Created by Stack on 5/4/20.
//
#include "../common/thread.h"
#include "../libITG/ITGapi.h"
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <string>
#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <sys/stat.h>
#include "../common/json.hpp"

#ifdef UNIX


#include <random>
#include <thread>
#include <chrono>
#include <vector>
#include <fstream>
#include <iostream>

#endif
#ifndef SRC_SOCKET_UTIL_H

using json=nlohmann::json;
using string=std::string;
using ip_addrs=std::vector<string>;

bool report_to_controller(char* dst_ip,int dst_port,json& obj);

void read_ip_files(string& fn,string& self_ip,ip_addrs& others);


void append_params(std::string &command, std::string key, std::string value);

inline bool file_exists(const string& fn){
    struct stat buffer;
    return ((stat(fn.c_str(),&buffer))==0);
}
inline bool file_exists(const char *fn){
    struct stat buffer;
    return ((stat(fn,&buffer))==0);
}
inline bool dir_exists(const char* dirn){
    struct stat buffer;
    if(stat(dirn,&buffer)!=0){
        return false;
    }
    if(buffer.st_mode&S_IFDIR){
        return true;
    }
    return false;
}
inline bool dir_exists(const string& dirn){
  return dir_exists(dirn.c_str());
}

template<class... Args>
inline void print_error(const char* module,Args... msgs){
    std::cout<<module<<" Error ";
    for(auto& x:{msgs...}){
       std::cout<<x<<" ";
    }
    std::cout<<std::endl;
}

inline void print_error(const char* module,const char* msg){
    std::cout<<"Error: "<<module<<": "<<std::endl;
}

inline void print_error(const char* module,const char* m1,const char* m2){
    std::cout<<"Error: "<<module<<": "<<m1<<" "<<m2<<std::endl;
}

inline void print_msg(const char* module,const char* msg){
    std::cout<<"Info: "<<module<<": "<<msg<<std::endl;
}

inline void print_msg(const char* module,const char* m1,const char* m2){
    std::cout<<"Info: "<<module<<": "<<m1<<" "<<m2<<std::endl;
}


#define SRC_SOCKET_UTIL_H

#endif //SRC_SOCKET_UTIL_H
