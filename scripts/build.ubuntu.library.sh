#!/bin/bash
set -xe

# 安装必要的工具和库
sudo add-apt-repository ppa:ubuntu-toolchain-r/test -y
sudo apt update

sudo apt install g++-13 -y
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100


sudo apt update
sudo apt install gcc g++ build-essential cmake make autoconf automake libtool python3 -y
sudo apt install libmbedtls-dev zlib1g-dev rapidjson-dev libpcre2-dev -y

# 构建并安装静态版本的 curl
git clone https://github.com/curl/curl --depth=1 --branch curl-8_4_0
cd curl
cmake -DCURL_USE_MBEDTLS=ON -DHTTP_ONLY=ON -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DCMAKE_USE_LIBSSH2=OFF -DBUILD_CURL_EXE=OFF .
make install -j$(nproc)
cd ..

# 构建并安装静态版本的 yaml-cpp
git clone https://github.com/jbeder/yaml-cpp --depth=1
cd yaml-cpp
cmake -DCMAKE_BUILD_TYPE=Release -DYAML_CPP_BUILD_TESTS=OFF -DYAML_CPP_BUILD_TOOLS=OFF -DBUILD_SHARED_LIBS=OFF .
make install -j$(nproc)
cd ..

# 构建并安装静态版本的 quickjspp
git clone https://github.com/ftk/quickjspp --depth=1
cd quickjspp
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF .
make quickjs -j$(nproc)
install -d /usr/lib/quickjs/
install -m644 quickjs/libquickjs.a /usr/lib/quickjs/
install -d /usr/include/quickjs/
install -m644 quickjs/quickjs.h quickjs/quickjs-libc.h /usr/include/quickjs/
install -m644 quickjspp.hpp /usr/include/
cd ..

# 构建并安装静态版本的 libcron
git clone https://github.com/PerMalmberg/libcron --depth=1
cd libcron
git submodule update --init
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF .
make libcron install -j$(nproc)
cd ..

# 构建并安装静态版本的 toml11
git clone https://github.com/ToruNiina/toml11 --branch="v3.7.1" --depth=1
cd toml11
cmake -DCMAKE_CXX_STANDARD=11 -DBUILD_SHARED_LIBS=OFF .
make install -j$(nproc)
cd ..

# 构建 subconverter 静态库
export PKG_CONFIG_PATH=/usr/lib64/pkgconfig
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_STATIC_LIBRARY=ON .
make -j$(nproc)