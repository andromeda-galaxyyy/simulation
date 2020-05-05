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


#include "DummyManager.h"
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

bool report_to_controller(char *dst_ip, int dst_port, json &obj) {
    int sockfd;
    struct sockaddr_in servaddr;
    memset(&servaddr, 0, sizeof(sockaddr_in));
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(dst_port);
    inet_pton(AF_INET, dst_ip, &(servaddr.sin_addr));

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        perror("Cannot create socket \n");
        return false;
    }
    if (connect(sockfd, (struct sockaddr *) &servaddr, sizeof(servaddr)) < 0) {
        perror("Cannot connect to remote ip:");
        printf("%s\n", dst_ip);
        return false;
    }
    string content = obj.dump();
    return send(sockfd, content.c_str(), content.size(), MSG_CONFIRM);
}
#define SRC_SOCKET_UTIL_H

#endif //SRC_SOCKET_UTIL_H
