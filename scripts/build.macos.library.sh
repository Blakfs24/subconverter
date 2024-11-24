#!/bin/bash
set -xe

# Install required tools and libraries
brew reinstall rapidjson zlib pcre2 pkgconfig

# Build and install yaml-cpp static library
git clone https://github.com/jbeder/yaml-cpp --depth=1
cd yaml-cpp
cmake -DCMAKE_BUILD_TYPE=Release -DYAML_CPP_BUILD_TESTS=OFF -DYAML_CPP_BUILD_TOOLS=OFF -DBUILD_SHARED_LIBS=OFF .
make -j4
sudo make install
cd ..

# Build and install quickjspp static library
# git clone https://github.com/ftk/quickjspp --depth=1
# cd quickjspp
# cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF .
# make quickjs -j
# sudo install -d /usr/local/lib/quickjs/
# sudo install -m644 quickjs/libquickjs.a /usr/local/lib/quickjs/
# sudo install -d /usr/local/include/quickjs/
# sudo install -m644 quickjs/quickjs.h quickjs/quickjs-libc.h /usr/local/include/quickjs/
# sudo install -m644 quickjspp.hpp /usr/local/include/
# cd ..

# Build and install libcron static library
# git clone https://github.com/PerMalmberg/libcron --depth=1
# cd libcron
# git submodule update --init
# cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF .
# make libcron -j4
# sudo install -m644 libcron/out/Release/liblibcron.a /usr/local/lib/
# sudo install -d /usr/local/include/libcron/
# sudo install -m644 libcron/include/libcron/* /usr/local/include/libcron/
# sudo install -d /usr/local/include/date/
# sudo install -m644 libcron/externals/date/include/date/* /usr/local/include/date/
# cd ..

# Build and install toml11 static library
git clone https://github.com/ToruNiina/toml11 --branch="v3.7.1" --depth=1
cd toml11
cmake -DCMAKE_CXX_STANDARD=11 -DBUILD_SHARED_LIBS=OFF .
sudo make install -j4
cd ..

# Build subconverter static library
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_STATIC_LIBRARY=ON .
make -j4
