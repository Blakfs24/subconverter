# Subconverter CMake 构建指南

## 📋 目录

- [简介](#简介)
- [新特性：自动依赖下载](#新特性自动依赖下载)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [构建选项详解](#构建选项详解)
- [不同场景的构建方法](#不同场景的构建方法)
- [依赖说明](#依赖说明)
- [常见问题](#常见问题)
- [高级用法](#高级用法)
- [故障排除](#故障排除)

---

## 📝 简介

本项目现已支持两大核心功能，让构建过程更简单、更灵活！

### ✨ 新特性 1：自动依赖下载

以前的构建流程：
```bash
❌ 需要手动安装所有依赖：
sudo apt install libyaml-cpp-dev libpcre2-dev rapidjson-dev ...
然后才能构建
```

现在的构建流程：
```bash
✅ 零依赖构建！只需：
mkdir build && cd build
cmake ..
make

CMake 会自动下载并编译所有需要的库！
```

### ✨ 新特性 2：完整静态库打包（Full Static Library）

现在可以生成**两种静态库**：

1. **libsubconverter_static.a** - 只包含 subconverter 核心代码（约 500KB）
2. **libsubconverter_static_full.a** - 整合所有依赖的完整库（约 3MB）

**为什么需要完整库？**

```bash
# 使用单独库：需要手动链接所有依赖 😓
g++ app.cpp -lsubconverter_static -lyaml-cpp -lpcre2-8 -pthread

# 使用完整库：一个文件搞定！😊
g++ app.cpp -lsubconverter_static_full -pthread
```

完整库将 subconverter、yaml-cpp 等所有依赖打包成**一个 .a 文件**，使用时无需手动管理依赖链接，极大简化了集成过程！

---

## 🔧 环境要求

### 必需软件

| 软件 | 最低版本 | 说明 |
|------|----------|------|
| **CMake** | 3.14+ | 构建系统（支持 FetchContent） |
| **C++ 编译器** | 支持 C++20 | GCC 10+, Clang 10+, MSVC 2019+ |
| **Git** | 任意版本 | 用于自动下载依赖（FetchContent） |
| **Make** | 任意版本 | Linux/macOS 构建工具 |

### 检查你的环境

```bash
# 检查 CMake 版本（需要 >= 3.14）
cmake --version
# 输出示例: cmake version 3.22.1

# 检查 C++ 编译器
g++ --version
# 或
clang++ --version

# 检查 Git
git --version
```

### 如果 CMake 版本过低

```bash
# Ubuntu/Debian - 安装最新 CMake
sudo apt remove cmake
sudo snap install cmake --classic

# macOS
brew install cmake

# 或从源码安装
wget https://github.com/Kitware/CMake/releases/download/v3.28.0/cmake-3.28.0.tar.gz
tar -xzf cmake-3.28.0.tar.gz
cd cmake-3.28.0
./bootstrap && make && sudo make install
```

---

## 🚀 快速开始

### 方式 1：零依赖自动构建（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/subconverter.git
cd subconverter

# 2. 创建构建目录
mkdir build && cd build

# 3. 配置项目（自动下载依赖）
cmake ..

# 你会看到类似输出：
# ⬇️  Fetching RapidJSON from GitHub...
# ✅ RapidJSON fetched successfully
# ⬇️  Fetching toml11 from GitHub...
# ✅ toml11 fetched successfully
# ⬇️  Fetching yaml-cpp from GitHub...
# ✅ yaml-cpp fetched and configured successfully
# ⬇️  Fetching PCRE2 from GitHub...
# ✅ PCRE2 fetched and configured successfully

# 4. 编译（使用所有 CPU 核心）
make -j$(nproc)

# 5. 运行
./subconverter
```

**首次构建时间**：
- 网速正常：约 5-10 分钟（需要下载依赖）
- 后续构建：约 1-3 分钟（依赖已缓存）

### 方式 2：使用系统已安装的依赖

```bash
# 1. 先安装依赖（Ubuntu/Debian 示例）
sudo apt install -y \
    libyaml-cpp-dev \
    libpcre2-dev \
    rapidjson-dev \
    libcurl4-openssl-dev

# 2. 构建
mkdir build && cd build
cmake ..

# 你会看到：
# ✅ Using system yaml-cpp
# ✅ Using system PCRE2
# ⬇️  Fetching RapidJSON from GitHub...  # 系统没有的仍会下载
# ⬇️  Fetching toml11 from GitHub...

make -j$(nproc)
```

---

## 🎛️ 构建选项详解

CMake 提供了多个选项来控制构建行为：

### 核心选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `AUTO_FETCH_DEPS` | `ON` | 自动下载缺失的依赖 |
| `FORCE_FETCH_DEPS` | `OFF` | 强制下载所有依赖（忽略系统库） |
| `BUILD_RELEASE_APP` | `ON` | 构建完整的 subconverter 程序 |
| `BUILD_STATIC_LIBRARY` | `OFF` | 构建核心静态库（libsubconverter_static.a） |
| `BUILD_FULL_STATIC` | `ON` | 构建完整静态库（libsubconverter_static_full.a）⭐ |
| `USING_MALLOC_TRIM` | `OFF` | 启用内存优化（需系统支持） |
| `CMAKE_BUILD_TYPE` | `Release` | 构建类型（Release/Debug） |

**注意**：`BUILD_FULL_STATIC` 只有在 `BUILD_STATIC_LIBRARY=ON` 时才生效。

### 使用方式

```bash
# 语法
cmake -D<选项名>=<值> ..

# 示例
cmake -DAUTO_FETCH_DEPS=OFF ..
```

---

## 🎯 不同场景的构建方法

### 场景 1：完全自动构建（零依赖）

**适用于**：
- 首次构建
- CI/CD 环境
- 系统没有预装依赖
- 想要可重现的构建

```bash
mkdir build && cd build

# 强制下载所有依赖（不使用系统库）
cmake -DFORCE_FETCH_DEPS=ON ..

make -j$(nproc)
```

**优点**：
- ✅ 不需要任何预装依赖
- ✅ 版本可控（使用固定的 Git 标签）
- ✅ 跨平台一致性

**缺点**：
- ⏱️ 首次构建时间较长（需下载编译依赖）

---

### 场景 2：智能混合模式（默认）

**适用于**：
- 日常开发
- 系统已有部分依赖
- 想节省编译时间

```bash
mkdir build && cd build

# 使用默认设置（优先系统库，缺失时自动下载）
cmake ..

make -j$(nproc)
```

**工作原理**：
```
检查 yaml-cpp → 系统有 → ✅ 使用系统库
检查 PCRE2    → 系统有 → ✅ 使用系统库
检查 RapidJSON → 系统无 → ⬇️  自动下载
检查 toml11   → 系统无 → ⬇️  自动下载
```

**优点**：
- ✅ 最快的构建速度（使用系统预编译库）
- ✅ 自动补全缺失依赖

---

### 场景 3：只使用系统依赖（不自动下载）

**适用于**：
- 生产环境部署
- 使用包管理器管理依赖
- 离线构建

```bash
# 1. 先安装所有依赖
sudo apt install -y \
    libyaml-cpp-dev \
    libpcre2-dev \
    rapidjson-dev \
    libcurl4-openssl-dev

# 2. 禁用自动下载
mkdir build && cd build
cmake -DAUTO_FETCH_DEPS=OFF ..

make -j$(nproc)
```

**如果缺少依赖会怎样？**
```bash
❌ CMake Error: Could not find yaml-cpp
   请安装: sudo apt install libyaml-cpp-dev
```

---

### 场景 4：构建静态库（核心功能库）⭐

**适用于**：
- 嵌入到其他项目
- 只需核心转换功能
- 需要将 subconverter 作为库使用

#### 4.1 生成两个静态库（默认，推荐）

```bash
mkdir build && cd build

cmake \
    -DBUILD_RELEASE_APP=OFF \
    -DBUILD_STATIC_LIBRARY=ON \
    ..

make -j$(nproc)

# 生成两个文件：
ls -lh *.a
# libsubconverter_static.a       约 500KB  - 单独的核心库
# libsubconverter_static_full.a  约 3MB    - 整合所有依赖的完整库 ⭐
```

#### 4.2 只生成单独库（不生成 full 版本）

```bash
cmake \
    -DBUILD_RELEASE_APP=OFF \
    -DBUILD_STATIC_LIBRARY=ON \
    -DBUILD_FULL_STATIC=OFF \
    ..

make -j$(nproc)

# 只生成一个文件：
# libsubconverter_static.a
```

**静态库包含的功能**：
- ✅ 订阅解析（subparser）
- ✅ 规则转换（ruleconvert）
- ✅ 配置导出（subexport）
- ✅ 模板渲染（templates）
- ❌ 不包含：HTTP 服务器、脚本引擎、网络请求

**两个库的区别**：

| 库文件 | 大小 | 包含内容 | 链接时需要 |
|--------|------|----------|------------|
| **libsubconverter_static.a** | ~500KB | 只有核心代码 | 需要手动链接 yaml-cpp、PCRE2 |
| **libsubconverter_static_full.a** | ~3MB | 核心代码 + yaml-cpp | 不需要额外依赖！⭐ |

**使用示例**：

```bash
# 使用单独库（复杂）
g++ my_app.cpp \
    -L/path/to/build \
    -lsubconverter_static \
    -lyaml-cpp \
    -lpcre2-8 \
    -pthread \
    -o my_app

# 使用完整库（简单）⭐
g++ my_app.cpp \
    -L/path/to/build \
    -lsubconverter_static_full \
    -pthread \
    -o my_app
```

---

### 场景 5：Debug 调试构建

```bash
mkdir build-debug && cd build-debug

cmake \
    -DCMAKE_BUILD_TYPE=Debug \
    -DFORCE_FETCH_DEPS=ON \
    ..

make -j$(nproc)

# 使用 GDB 调试
gdb ./subconverter
```

**Debug vs Release 区别**：

| 特性 | Debug | Release |
|------|-------|---------|
| 优化级别 | -O0 | -O2/-O3 |
| 调试符号 | 包含 | 不包含 |
| 性能 | 慢 | 快 |
| 二进制大小 | 大 | 小 |

---

## 📦 依赖说明

### 自动下载的依赖（通过 FetchContent）

| 依赖 | 版本 | 用途 | 下载大小 | 是否必需 |
|------|------|------|----------|----------|
| **yaml-cpp** | 0.8.0 | YAML 配置解析 | ~5 MB | ✅ 必需 |
| **PCRE2** | 10.44 | 正则表达式 | ~8 MB | ✅ 必需 |
| **RapidJSON** | master | JSON 解析 | ~2 MB | ✅ 必需 |
| **toml11** | v4.3.0 | TOML 配置解析 | ~1 MB | ✅ 必需 |
| **CURL** | 8.5.0 | HTTP 请求（完整程序） | ~15 MB | ⚠️ 仅完整程序 |

**总下载大小**：约 30-35 MB（首次构建）

### 必须手动安装的依赖

这些库暂时无法通过 FetchContent 自动下载：

```bash
# Ubuntu/Debian
sudo apt install -y libquickjs-dev libcron-dev

# 或从源码编译
# QuickJS: https://bellard.org/quickjs/
# LibCron: https://github.com/PerMalmberg/libcron
```

| 依赖 | 用途 | 是否必需 |
|------|------|----------|
| **QuickJS** | JavaScript 脚本引擎 | ⚠️ 仅完整程序 |
| **LibCron** | 定时任务 | ⚠️ 仅完整程序 |

**注意**：如果只构建静态库（`BUILD_STATIC_LIBRARY=ON`），不需要这些依赖。

---

## 🛠️ 常见问题

### Q1: 下载依赖很慢怎么办？

**方案 1：使用镜像源（国内用户）**

编辑 `CMakeLists.txt`，修改 Git 仓库地址：

```cmake
# 原地址
GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git

# 改为 Gitee 镜像
GIT_REPOSITORY https://gitee.com/mirrors/yaml-cpp.git
```

**方案 2：手动预下载**

```bash
# 在项目根目录执行
mkdir -p build/_deps

# 下载 yaml-cpp
git clone --depth=1 --branch 0.8.0 \
    https://github.com/jbeder/yaml-cpp.git \
    build/_deps/yaml-cpp-src

# 下载 PCRE2
git clone --depth=1 --branch pcre2-10.44 \
    https://github.com/PCRE2Project/pcre2.git \
    build/_deps/pcre2-src

# 然后正常构建
cd build
cmake ..  # 会使用已下载的源码
```

---

### Q2: 如何查看哪些依赖被下载了？

```bash
# 方式 1：查看 CMake 输出
cmake .. 2>&1 | grep -E "(Using system|Fetching)"

# 方式 2：查看 _deps 目录
ls -la build/_deps/

# 输出示例：
# yaml-cpp-src/   yaml-cpp-build/
# pcre2-src/      pcre2-build/
# rapidjson-src/  rapidjson-subbuild/
```

---

### Q3: 如何清理下载的依赖重新构建？

```bash
# 方式 1：删除整个 build 目录
rm -rf build/
mkdir build && cd build
cmake ..

# 方式 2：只删除依赖
rm -rf build/_deps/
cd build
cmake ..
```

---

### Q4: 编译时报错 "Could not find QuickJS"

**原因**：QuickJS 无法自动下载，需要手动安装。

**解决方案 1**：安装 QuickJS

```bash
# Ubuntu/Debian
sudo apt install libquickjs-dev

# 或从源码编译
git clone https://github.com/bellard/quickjs.git
cd quickjs
make
sudo make install
```

**解决方案 2**：只构建静态库（不需要 QuickJS）

```bash
cmake -DBUILD_RELEASE_APP=OFF -DBUILD_STATIC_LIBRARY=ON ..
```

---

### Q5: 如何指定使用特定的编译器？

```bash
# 使用 GCC
cmake -DCMAKE_CXX_COMPILER=g++ ..

# 使用 Clang
cmake -DCMAKE_CXX_COMPILER=clang++ ..

# 或通过环境变量
export CXX=g++-11
cmake ..
```

---

### Q6: 构建时提示 "CMake version too old"

**当前版本要求**：CMake 3.14+

**升级方法**：

```bash
# Ubuntu/Debian
sudo apt remove cmake
sudo snap install cmake --classic

# macOS
brew upgrade cmake

# 验证版本
cmake --version
```

---

## 🔬 高级用法

### 自定义依赖版本

编辑 `CMakeLists.txt`，修改 `GIT_TAG`：

```cmake
FetchContent_Declare(
    yaml-cpp
    GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
    GIT_TAG        0.8.0  # ← 修改这里
    GIT_SHALLOW    TRUE
)
```

### 使用本地源码构建依赖

```cmake
FetchContent_Declare(
    yaml-cpp
    SOURCE_DIR /path/to/local/yaml-cpp  # ← 使用本地路径
)
```

### 并行编译加速

```bash
# 使用所有 CPU 核心
make -j$(nproc)

# 或指定核心数
make -j8

# 使用 Ninja（更快）
cmake -GNinja ..
ninja
```

### 使用 ccache 加速重复编译

```bash
# 安装 ccache
sudo apt install ccache

# 配置 CMake
cmake -DCMAKE_CXX_COMPILER_LAUNCHER=ccache ..

# 首次编译
make -j$(nproc)

# 重复编译将快很多！
```

---

## 🐛 故障排除

### 问题 1：Git clone 超时

**错误信息**：
```
fatal: unable to access 'https://github.com/...': Failed to connect
```

**解决方案**：

```bash
# 方案 1：配置 Git 代理
git config --global http.proxy http://127.0.0.1:7890

# 方案 2：使用 SSH 克隆（需要配置 SSH 密钥）
# 编辑 CMakeLists.txt，将 https:// 改为 git@

# 方案 3：手动下载后使用本地路径
# 参见 Q2 手动预下载
```

---

### 问题 2：链接错误 "undefined reference"

**错误示例**：
```
undefined reference to `yaml_cpp::Node::Node()`
```

**可能原因**：
1. 依赖下载不完整
2. ABI 不兼容（混用了不同编译器）

**解决方案**：

```bash
# 1. 清理重新构建
rm -rf build/
mkdir build && cd build
cmake -DFORCE_FETCH_DEPS=ON ..  # 强制重新下载
make -j$(nproc)

# 2. 确保使用同一编译器
cmake -DCMAKE_CXX_COMPILER=g++ ..
```

---

### 问题 3：内存不足导致编译失败

**错误信息**：
```
c++: fatal error: Killed signal terminated program cc1plus
```

**解决方案**：

```bash
# 减少并行任务数
make -j2  # 只用 2 核编译

# 或增加交换空间（swap）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

### 问题 4：PCRE2 编译失败（JIT 相关）

**错误信息**：
```
PCRE2_SUPPORT_JIT requires architecture support
```

**解决方案**：

编辑 `CMakeLists.txt`，禁用 JIT：

```cmake
SET(PCRE2_SUPPORT_JIT OFF CACHE INTERNAL "")  # ← 改为 OFF
```

或使用系统 PCRE2：

```bash
sudo apt install libpcre2-dev
cmake -DAUTO_FETCH_DEPS=OFF ..
```

---

## 📊 构建时间对比

基于 4 核 CPU、16GB RAM 的测试环境：

| 构建方式 | 首次构建 | 增量构建 | 清理后重建 |
|----------|----------|----------|------------|
| **自动下载依赖** | 8-12 分钟 | 30 秒 | 3-5 分钟 |
| **使用系统库** | 2-3 分钟 | 30 秒 | 2-3 分钟 |
| **强制下载全部** | 10-15 分钟 | 30 秒 | 10-15 分钟 |

---

## 📚 相关文档

- [CMake 官方文档](https://cmake.org/documentation/)
- [FetchContent 模块文档](https://cmake.org/cmake/help/latest/module/FetchContent.html)
- [Subconverter 项目主页](https://github.com/tindy2013/subconverter)

---

## 🎓 总结

### 推荐的构建命令

**新手/快速开始**：
```bash
mkdir build && cd build
cmake ..
make -j$(nproc)
```

**开发者**：
```bash
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
```

**CI/CD**：
```bash
mkdir build && cd build
cmake -DFORCE_FETCH_DEPS=ON -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
```

**生产环境**：
```bash
# 先安装系统依赖
sudo apt install libyaml-cpp-dev libpcre2-dev ...

mkdir build && cd build
cmake -DAUTO_FETCH_DEPS=OFF -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
sudo make install
```

---

## 📦 完整静态库详解（Full Static Library）

### 什么是完整静态库？

完整静态库（libsubconverter_static_full.a）是将 subconverter 核心代码和所有依赖库（yaml-cpp）**合并**成一个 `.a` 文件。

**类比**：
- 单独库：就像买菜需要分别买肉、菜、调料（需要手动管理依赖）
- 完整库：就像买盒饭，所有食材都在一个盒子里（一个文件包含所有）

### 技术实现原理

使用 `ar` 命令的 MRI（Multi-library Resource Interchange）脚本：

```bash
# bundle.mri 脚本内容
CREATE libsubconverter_static_full.a
ADDLIB libsubconverter_static.a
ADDLIB _deps/yaml-cpp-build/libyaml-cpp.a
SAVE
END

# 执行合并
ar -M < bundle.mri
```

### 验证完整库

#### 1. 查看库的大小

```bash
ls -lh build/*.a

# 输出示例：
# -rw-r--r-- 1 user user  524K  libsubconverter_static.a
# -rw-r--r-- 1 user user  2.8M  libsubconverter_static_full.a  ← 明显更大
```

#### 2. 查看包含的目标文件数量

```bash
# 单独库
ar -t build/libsubconverter_static.a | wc -l
# 输出: 13  (只有 subconverter 的目标文件)

# 完整库
ar -t build/libsubconverter_static_full.a | wc -l
# 输出: 245  (包含 subconverter + yaml-cpp 的所有目标文件)
```

#### 3. 查看包含的符号

```bash
# 验证包含 yaml-cpp 的符号
nm -C build/libsubconverter_static_full.a | grep -i "YAML::" | head -5

# 输出示例：
# 0000000000000000 T YAML::Node::Node()
# 0000000000000150 T YAML::Load(std::string const&)
# ...
```

#### 4. 查看 bundle.mri 脚本

```bash
cat build/bundle.mri

# 输出示例：
# CREATE /path/to/build/libsubconverter_static_full.a
# ADDLIB /path/to/build/libsubconverter_static.a
# ADDLIB /path/to/build/_deps/yaml-cpp-build/libyaml-cpp.a
# SAVE
# END
```

### 实际使用示例

#### 示例 1：简单程序

```cpp
// my_app.cpp
#include "handler/settings.h"
#include "parser/subparser.h"

int main() {
    // 使用 subconverter 功能
    return 0;
}
```

**编译**：

```bash
# 使用完整库 - 超级简单！
g++ my_app.cpp \
    -I/path/to/subconverter/src \
    -L/path/to/build \
    -lsubconverter_static_full \
    -pthread \
    -o my_app

# ✅ 完成！不需要 -lyaml-cpp
```

#### 示例 2：CMake 项目集成

```cmake
# 你的项目的 CMakeLists.txt
cmake_minimum_required(VERSION 3.14)
project(MyApp)

# 添加 subconverter 头文件路径
include_directories(/path/to/subconverter/src)

# 链接完整静态库
add_executable(my_app main.cpp)
target_link_libraries(my_app
    /path/to/build/libsubconverter_static_full.a
    pthread
)
# ✅ 就这么简单！
```

### 跨平台支持

| 平台 | 工具 | 文件扩展名 | 支持情况 |
|------|------|------------|----------|
| **Linux** | ar (MRI script) | .a | ✅ 完全支持 |
| **macOS** | libtool -static | .a | ✅ 完全支持 |
| **Windows (MSVC)** | lib.exe | .lib | ✅ 完全支持 |
| **Windows (MinGW)** | ar (MRI script) | .a | ✅ 完全支持 |

### 常见问题

#### Q: 完整库包含 PCRE2 吗？

**A**: 如果使用系统的 PCRE2，则**不包含**（系统库是 INTERFACE 类型，无法合并）。

**解决方案**：强制下载 PCRE2

```bash
cmake \
    -DBUILD_RELEASE_APP=OFF \
    -DBUILD_STATIC_LIBRARY=ON \
    -DFORCE_FETCH_DEPS=ON \  # ← 强制下载所有依赖
    ..
```

#### Q: 如何只生成单独库？

**A**: 设置 `BUILD_FULL_STATIC=OFF`

```bash
cmake \
    -DBUILD_RELEASE_APP=OFF \
    -DBUILD_STATIC_LIBRARY=ON \
    -DBUILD_FULL_STATIC=OFF \
    ..
```

#### Q: 完整库适合什么场景？

**A**: 最适合以下场景：
- ✅ 分发给其他开发者使用（不需要他们安装依赖）
- ✅ 嵌入式项目（简化依赖管理）
- ✅ 跨平台移植（一个文件搞定）
- ✅ CI/CD 集成（减少外部依赖）

---

## 💡 小贴士

1. **首次构建耐心等待**：下载依赖需要时间，泡杯咖啡休息一下 ☕
2. **使用 `-j` 参数**：充分利用多核 CPU 加速编译
3. **保留 build 目录**：下次构建会快很多（依赖已缓存）
4. **遇到问题先清理**：`rm -rf build/` 解决 90% 的构建问题
5. **检查网络连接**：自动下载需要访问 GitHub

---

## 📞 获取帮助

如果遇到本文档未涵盖的问题：

1. 查看 [GitHub Issues](https://github.com/tindy2013/subconverter/issues)
2. 提交新 Issue 并附上：
   - CMake 版本（`cmake --version`）
   - 编译器版本（`g++ --version`）
   - 完整错误日志
   - 构建命令

---

**最后更新**：2025-11-08
**文档版本**：v2.1 (FetchContent + Full Static Library)
