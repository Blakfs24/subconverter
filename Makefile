# Generic Makefile for building the subconverter static library.
# The goal matches the BUILD_STATIC_LIBRARY option in CMakeLists.txt, but lets you
# build the core as libsubconverter.{a,lib} with plain make on Linux/macOS/MinGW.

LIB_NAME        ?= subconverter
BUILD_DIR       ?= build/
OBJ_DIR         := $(BUILD_DIR)/obj
DEPS_DIR        ?= $(BUILD_DIR)/deps
DEPS_SRC_DIR    := $(DEPS_DIR)/src
DEPS_BUILD_DIR  := $(DEPS_DIR)/build
DEPS_INSTALL_DIR:= $(DEPS_DIR)/install
DEPS_STAMP_DIR  := $(DEPS_DIR)/stamps

# Detect platform so we can pick sensible defaults (e.g. -fPIC).
OS_GUESS        := $(strip $(if $(OS),$(OS),$(shell uname -s 2>/dev/null || echo unknown)))
ifeq ($(OS_GUESS),Windows_NT)
    PLATFORM := windows
else ifneq (,$(findstring MINGW,$(OS_GUESS)))
    PLATFORM := windows
else ifneq (,$(findstring MSYS,$(OS_GUESS)))
    PLATFORM := windows
else ifeq ($(OS_GUESS),Darwin)
    PLATFORM := macos
else
    PLATFORM := linux
endif

ifeq ($(PLATFORM),windows)
    PIC_FLAG ?=
    STATIC_LIB_PREFIX ?= lib
else
    PIC_FLAG ?= -fPIC
    STATIC_LIB_PREFIX ?= lib
endif

STATIC_LIB_EXT  ?= a
STATIC_LIB      ?= $(BUILD_DIR)/$(STATIC_LIB_PREFIX)$(LIB_NAME).$(STATIC_LIB_EXT)
FULL_STATIC_LIB ?= $(BUILD_DIR)/$(STATIC_LIB_PREFIX)$(LIB_NAME)_full.$(STATIC_LIB_EXT)

CXX             ?= g++
AR              ?= ar
ARFLAGS         ?= rcs
GIT             ?= git
CMAKE           ?= cmake

# Third-party dependency revisions (match scripts/ recipes where possible)
YAML_CPP_REPO   ?= https://github.com/jbeder/yaml-cpp.git
YAML_CPP_TAG    ?=
PCRE2_REPO      ?= https://github.com/PCRE2Project/pcre2.git
PCRE2_TAG       ?= pcre2-10.44
RAPIDJSON_REPO  ?= https://github.com/Tencent/rapidjson.git
RAPIDJSON_TAG   ?= 
TOML11_REPO     ?= https://github.com/ToruNiina/toml11.git
TOML11_TAG      ?= v4.3.0

YAML_CPP_BRANCH_ARG := $(if $(strip $(YAML_CPP_TAG)),--branch $(YAML_CPP_TAG),)
PCRE2_BRANCH_ARG    := $(if $(strip $(PCRE2_TAG)),--branch $(PCRE2_TAG),)
RAPIDJSON_BRANCH_ARG:= $(if $(strip $(RAPIDJSON_TAG)),--branch $(RAPIDJSON_TAG),)
TOML11_BRANCH_ARG   := $(if $(strip $(TOML11_TAG)),--branch $(TOML11_TAG),)

YAML_CPP_SRC_DIR    := $(DEPS_SRC_DIR)/yaml-cpp
PCRE2_SRC_DIR       := $(DEPS_SRC_DIR)/pcre2
RAPIDJSON_SRC_DIR   := $(DEPS_SRC_DIR)/rapidjson
TOML11_SRC_DIR      := $(DEPS_SRC_DIR)/toml11

LOCAL_LIB_DIR       := $(DEPS_INSTALL_DIR)/lib
LOCAL_INCLUDE_DIR   := $(DEPS_INSTALL_DIR)/include
ABS_DEPS_INSTALL_DIR:= $(abspath $(DEPS_INSTALL_DIR))
ABS_YAML_CPP_SRC_DIR:= $(abspath $(YAML_CPP_SRC_DIR))
ABS_PCRE2_SRC_DIR   := $(abspath $(PCRE2_SRC_DIR))
YAML_CPP_STATIC_LIB ?= $(LOCAL_LIB_DIR)/libyaml-cpp.a
PCRE2_STATIC_LIB    ?= $(LOCAL_LIB_DIR)/libpcre2-8.a

CXXSTD          ?= -std=c++20
WARNINGS        ?= -Wall -Wextra -Wno-unused-parameter -Wno-unused-result
OPTFLAGS        ?= -O2
DEPFLAGS        ?= -MMD -MP

CXXFLAGS        ?=
CXXFLAGS        += $(OPTFLAGS) $(WARNINGS) $(PIC_FLAG)
CXXFLAGS        += $(CXXSTD)

# Platform-specific compiler flags
ifeq ($(PLATFORM),macos)
    # macOS specific flags
    CXXFLAGS += -arch x86_64
    LDFLAGS ?=
    LDFLAGS += -arch x86_64 -isysroot $(shell xcrun --sdk macosx --show-sdk-path 2>/dev/null || echo "")
else
    LDFLAGS ?=
endif

CPPFLAGS        ?=
CPPFLAGS        += -Isrc -Iinclude \
                   -DNO_JS_RUNTIME -DNO_WEBGET \
                   -DYAML_CPP_STATIC_DEFINE -DPCRE2_STATIC \
                   -I$(LOCAL_INCLUDE_DIR)

# Allow callers to point to external headers without editing this file.
ifdef RAPIDJSON_INCLUDEDIR
    CPPFLAGS    += -I$(RAPIDJSON_INCLUDEDIR)
endif
ifdef TOML11_INCLUDEDIR
    CPPFLAGS    += -I$(TOML11_INCLUDEDIR)
endif
ifdef YAML_CPP_INCLUDEDIR
    CPPFLAGS    += -I$(YAML_CPP_INCLUDEDIR)
endif
ifdef PCRE2_INCLUDEDIR
    CPPFLAGS    += -I$(PCRE2_INCLUDEDIR)
endif

PKG_CONFIG      ?= pkg-config
PKG_CONFIG_AVAIL:= $(shell command -v $(PKG_CONFIG) >/dev/null 2>&1 && echo 1 || echo 0)
ifeq ($(PKG_CONFIG_AVAIL),1)
    YAML_CPP_CFLAGS ?= $(shell $(PKG_CONFIG) --cflags yaml-cpp 2>/dev/null)
    PCRE2_CFLAGS    ?= $(shell $(PKG_CONFIG) --cflags libpcre2-8 2>/dev/null)
endif
CPPFLAGS        += $(YAML_CPP_CFLAGS) $(PCRE2_CFLAGS)

# Core sources that constitute the static library (mirrors CMake's BUILD_STATIC_LIBRARY block).
SRCS := \
    src/generator/config/ruleconvert.cpp \
    src/generator/config/subexport.cpp \
    src/generator/template/templates.cpp \
    src/lib/wrapper.cpp \
    src/parser/subparser.cpp \
    src/utils/base64/base64.cpp \
    src/utils/codepage.cpp \
    src/utils/logger.cpp \
    src/utils/md5/md5.cpp \
    src/utils/network.cpp \
    src/utils/regexp.cpp \
    src/utils/string.cpp \
    src/utils/urlencode.cpp

OBJS := $(patsubst src/%.cpp,$(OBJ_DIR)/%.o,$(SRCS))
DEPS := $(OBJS:.o=.d)

.PHONY: all clean info deps deps-clean full-static

all: $(STATIC_LIB)

info:
	@echo "Platform      : $(PLATFORM)"
	@echo "CXX           : $(CXX)"
	@echo "CXXFLAGS      : $(CXXFLAGS)"
	@echo "CPPFLAGS      : $(CPPFLAGS)"
	@echo "Static library: $(STATIC_LIB)"

$(STATIC_LIB): $(OBJS)
	@mkdir -p $(dir $@)
	$(AR) $(ARFLAGS) $@ $^

$(OBJ_DIR)/%.o: src/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) $(DEPFLAGS) -c $< -o $@

clean:
	@rm -rf $(BUILD_DIR)

deps: $(YAML_CPP_STATIC_LIB) $(PCRE2_STATIC_LIB) \
      $(LOCAL_INCLUDE_DIR)/rapidjson/document.h \
      $(LOCAL_INCLUDE_DIR)/toml.hpp

deps-clean:
	@rm -rf $(DEPS_DIR)

full-static: deps $(FULL_STATIC_LIB)

$(FULL_STATIC_LIB): $(STATIC_LIB) $(YAML_CPP_STATIC_LIB) $(PCRE2_STATIC_LIB)
	@mkdir -p $(dir $@)
	@echo "create $@\naddlib $(STATIC_LIB)\naddlib $(YAML_CPP_STATIC_LIB)\naddlib $(PCRE2_STATIC_LIB)\nsave\nend" > $(BUILD_DIR)/bundle.mri
	$(AR) -M < $(BUILD_DIR)/bundle.mri

-include $(DEPS)

# -------------------------------------------------------------------
# Dependency build rules (yaml-cpp, PCRE2, RapidJSON, toml11)
# -------------------------------------------------------------------
$(DEPS_SRC_DIR):
	@mkdir -p $@

$(DEPS_STAMP_DIR):
	@mkdir -p $@

$(YAML_CPP_SRC_DIR)/.git: | $(DEPS_SRC_DIR)
	$(GIT) clone --depth=1 $(YAML_CPP_BRANCH_ARG) $(YAML_CPP_REPO) $(YAML_CPP_SRC_DIR)

$(PCRE2_SRC_DIR)/.git: | $(DEPS_SRC_DIR)
	$(GIT) clone --depth=1 $(PCRE2_BRANCH_ARG) $(PCRE2_REPO) $(PCRE2_SRC_DIR)

$(RAPIDJSON_SRC_DIR)/.git: | $(DEPS_SRC_DIR)
	$(GIT) clone --depth=1 $(RAPIDJSON_BRANCH_ARG) $(RAPIDJSON_REPO) $(RAPIDJSON_SRC_DIR)

$(TOML11_SRC_DIR)/.git: | $(DEPS_SRC_DIR)
	$(GIT) clone --depth=1 $(TOML11_BRANCH_ARG) $(TOML11_REPO) $(TOML11_SRC_DIR)

$(DEPS_STAMP_DIR)/yaml-cpp: $(YAML_CPP_SRC_DIR)/.git | $(DEPS_STAMP_DIR)
	@mkdir -p $(DEPS_BUILD_DIR)/yaml-cpp
	cd $(DEPS_BUILD_DIR)/yaml-cpp && $(CMAKE) -DCMAKE_BUILD_TYPE=Release -DYAML_CPP_BUILD_TESTS=OFF -DYAML_CPP_BUILD_TOOLS=OFF -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_INSTALL_PREFIX=$(ABS_DEPS_INSTALL_DIR) $(ABS_YAML_CPP_SRC_DIR)
	cd $(DEPS_BUILD_DIR)/yaml-cpp && $(CMAKE) --build . --target install --config Release
	@touch $@

$(DEPS_STAMP_DIR)/pcre2: $(PCRE2_SRC_DIR)/.git | $(DEPS_STAMP_DIR)
	@mkdir -p $(DEPS_BUILD_DIR)/pcre2
	cd $(DEPS_BUILD_DIR)/pcre2 && $(CMAKE) -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DPCRE2_BUILD_TESTS=OFF -DPCRE2_BUILD_PCRE2_16=OFF -DPCRE2_BUILD_PCRE2_32=OFF -DPCRE2_BUILD_PCRE2GREP=OFF -DPCRE2_SUPPORT_JIT=ON -DCMAKE_INSTALL_PREFIX=$(ABS_DEPS_INSTALL_DIR) $(ABS_PCRE2_SRC_DIR)
	cd $(DEPS_BUILD_DIR)/pcre2 && $(CMAKE) --build . --target install --config Release
	@touch $@

$(DEPS_STAMP_DIR)/rapidjson: $(RAPIDJSON_SRC_DIR)/.git | $(DEPS_STAMP_DIR)
	@mkdir -p $(LOCAL_INCLUDE_DIR)
	rm -rf $(LOCAL_INCLUDE_DIR)/rapidjson
	cp -R $(RAPIDJSON_SRC_DIR)/include/rapidjson $(LOCAL_INCLUDE_DIR)/
	@touch $@

$(DEPS_STAMP_DIR)/toml11: $(TOML11_SRC_DIR)/.git | $(DEPS_STAMP_DIR)
	@mkdir -p $(LOCAL_INCLUDE_DIR)
	cp -f $(TOML11_SRC_DIR)/single_include/toml.hpp $(LOCAL_INCLUDE_DIR)/
	@touch $@

$(YAML_CPP_STATIC_LIB): $(DEPS_STAMP_DIR)/yaml-cpp
	@true

$(PCRE2_STATIC_LIB): $(DEPS_STAMP_DIR)/pcre2
	@true

$(LOCAL_INCLUDE_DIR)/rapidjson/document.h: $(DEPS_STAMP_DIR)/rapidjson
	@true

$(LOCAL_INCLUDE_DIR)/toml.hpp: $(DEPS_STAMP_DIR)/toml11
	@true
