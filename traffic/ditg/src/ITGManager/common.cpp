//
// Created by Stack on 5/5/20.
//

#include "common.h"

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


void append_params(std::string &command, std::string key, std::string value) {
    command.append(" ");
    command.append(key);
    command.append(" ");
    command.append(value);
}



