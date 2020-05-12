//
// Created by Stack on 5/5/20.
//

#include "common.h"
#define MODULE "Common"

// must make sure this is a valid file path
void read_ip_files(string &fn,std::string& self_ip,ip_addrs & others) {
    std::ifstream infile(fn);
    std::string line;
    while (std::getline(infile, line)) {
        if (self_ip == "") {
            self_ip = line;
            continue;
        }
        others.emplace_back(line);
    }
}


bool report_to_controller(const char *dst_ip, int dst_port, json &obj) {
    int sockfd;
    struct sockaddr_in servaddr;
    memset(&servaddr, 0, sizeof(sockaddr_in));
    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(dst_port);
    inet_pton(AF_INET, dst_ip, &(servaddr.sin_addr));

    sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) {
        print_error(MODULE,"Cannot create socket");
        return false;
    }
    if (connect(sockfd, (struct sockaddr *) &servaddr, sizeof(servaddr)) < 0) {
        close(sockfd);
        print_error(MODULE,"Cannot connect to remote ip:",dst_ip);
        return false;
    }
    string content=obj.dump();
    const char* content_p = content.c_str();
    size_t len=strlen(content_p);
    ssize_t sent=send(sockfd,content_p, len, MSG_CONFIRM);
    close(sockfd);
    return sent==len;
}


void append_params(std::string &command, std::string key, std::string value) {
    command.append(" ");
    command.append(key);
    command.append(" ");
    command.append(value);
}



