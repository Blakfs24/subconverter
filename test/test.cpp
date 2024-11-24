#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include "../src/utils/yamlcpp_extra.h"
#include "../src/parser/config/proxy.h"
#include "../src/parser/subparser.h"
#include "../src/generator/config/subexport.h"


std::vector<std::string> splitByNewline(const std::string& str) {
    std::vector<std::string> result;
    size_t start = 0;
    size_t end;

    // 循环查找换行符的位置
    while ((end = str.find('\n', start)) != std::string::npos) {
        result.push_back(str.substr(start, end - start));  // 获取从start到end的子字符串
        start = end + 1;  // 跳过换行符
    }

    // 处理最后一行（如果没有换行符）
    result.push_back(str.substr(start));

    return result;
}


// g++ -I../src -static -std=c++20 test.cpp -L../ -lsubconverter -lpcre2-8 -lyaml-cpp -lm -lpthread
int main() {
    std::ifstream file("/workspaces/singtools_private/config.yaml");
    // std::ifstream file("all.txt");
    if (!file) {
        std::cerr << "无法打开文件!" << std::endl;
        return 1;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();  // 将文件的内容读入到 stringstream 中
    std::string fileContent = buffer.str();  // 将 stringstream 转换为 string

    // // std::cout << fileContent << std::endl;  // 输出文件内容
    YAML::Node config = YAML::Load(fileContent);
    std::vector<Proxy> nodes;
    for (auto iter: config["proxies"]) {
        explodeString(YAML::Dump(iter), nodes, "clash");
        // std::cout << YAML::Dump(iter) << std::endl;
    }

    // auto nodes = explodeConfs(fileContent);
    // auto node = splitByNewline(fileContent);
    // for (auto iter: node) {
    //     explodeString(iter, nodes, "link");
    //     std::cout << iter << std::endl;
    // }
    for (auto node: nodes) {
        std::cout << nodeToSingbox(node) << std::endl;
    }
    file.close();
    return 0;
}
