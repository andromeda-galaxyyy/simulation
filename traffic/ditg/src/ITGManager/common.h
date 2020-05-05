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

#define SRC_SOCKET_UTIL_H

#endif //SRC_SOCKET_UTIL_H
