#!/bin/bash
set -xe

# 获取系统架构
ARCH=$(uname -m)

if [ "$ARCH" == "x86_64" ]; then
    TOOLCHAIN="mingw-w64-x86_64"
else
    TOOLCHAIN="mingw-w64-i686"
fi

# 安装必要的工具和库
pacman -S --needed --noconfirm base-devel ${TOOLCHAIN}-toolchain ${TOOLCHAIN}-cmake ${TOOLCHAIN}-nghttp2 ${TOOLCHAIN}-openssl

# 构建并安装静态版本的 curl
# git clone https://github.com/curl/curl --depth=1 --branch curl-8_8_0
# cd curl
# cmake -DCMAKE_BUILD_TYPE=Release \
#       -DCURL_USE_LIBSSH2=OFF \
#       -DHTTP_ONLY=ON \
#       -DCURL_USE_SCHANNEL=ON \
#       -DBUILD_SHARED_LIBS=OFF \
#       -DBUILD_CURL_EXE=OFF \
#       -DCMAKE_INSTALL_PREFIX="$MINGW_PREFIX" \
#       -G "Unix Makefiles" \
#       -DHAVE_LIBIDN2=OFF \
#       -DCURL_USE_LIBPSL=OFF \
#       -DCURL_STATICLIB=ON \
#       -DCURL_DISABLE_SOCKETPAIR=ON \
#       -DCURL_DISABLE_NONBLOCKING=ON .
# make install -j4
# cd ..

# 构建并安装静态版本的 yaml-cpp
git clone https://github.com/jbeder/yaml-cpp --depth=1
cd yaml-cpp
cmake -DCMAKE_BUILD_TYPE=Release \
      -DYAML_CPP_BUILD_TESTS=OFF \
      -DYAML_CPP_BUILD_TOOLS=OFF \
      -DBUILD_SHARED_LIBS=OFF \
      -DCMAKE_INSTALL_PREFIX="$MINGW_PREFIX" \
      -G "Unix Makefiles" .
make install -j4
cd ..

# 构建并安装静态版本的 quickjspp
# git clone https://github.com/ftk/quickjspp --depth=1
# cd quickjspp
# patch quickjs/quickjs-libc.c -i ../scripts/patches/0001-quickjs-libc-add-realpath-for-Windows.patch
# cmake -G "Unix Makefiles" \
#       -DCMAKE_BUILD_TYPE=Release \
#       -DBUILD_SHARED_LIBS=OFF .
# make quickjs -j4
# install -d "$MINGW_PREFIX/lib/quickjs/"
# install -m644 quickjs/libquickjs.a "$MINGW_PREFIX/lib/quickjs/"
# install -d "$MINGW_PREFIX/include/quickjs"
# install -m644 quickjs/quickjs.h quickjs/quickjs-libc.h "$MINGW_PREFIX/include/quickjs/"
# install -m644 quickjspp.hpp "$MINGW_PREFIX/include/"
# cd ..

# # 构建并安装静态版本的 libcron
# git clone https://github.com/PerMalmberg/libcron --depth=1
# cd libcron
# git submodule update --init
# cmake -G "Unix Makefiles" \
#       -DCMAKE_BUILD_TYPE=Release \
#       -DBUILD_SHARED_LIBS=OFF \
#       -DCMAKE_INSTALL_PREFIX="$MINGW_PREFIX" .
# make libcron install -j4
# cd ..

# 构建并安装静态版本的 rapidjson
git clone https://github.com/Tencent/rapidjson --depth=1
cd rapidjson
cmake -DRAPIDJSON_BUILD_DOC=OFF \
      -DRAPIDJSON_BUILD_EXAMPLES=OFF \
      -DRAPIDJSON_BUILD_TESTS=OFF \
      -DBUILD_SHARED_LIBS=OFF \
      -DCMAKE_INSTALL_PREFIX="$MINGW_PREFIX" \
      -G "Unix Makefiles" .
make install -j4
cd ..

# 构建并安装静态版本的 toml11
git clone https://github.com/ToruNiina/toml11 --branch="v3.7.1" --depth=1
cd toml11
cmake -DCMAKE_INSTALL_PREFIX="$MINGW_PREFIX" \
      -G "Unix Makefiles" \
      -DCMAKE_CXX_STANDARD=11 \
      -DBUILD_SHARED_LIBS=OFF .
make install -j4
cd ..

# 构建 subconverter 静态库
rm -f C:/Strawberry/perl/bin/pkg-config C:/Strawberry/perl/bin/pkg-config.bat
cmake -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_STATIC_LIBRARY=ON \
      -G "Unix Makefiles" .
make -j4
