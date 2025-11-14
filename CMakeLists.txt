CMAKE_MINIMUM_REQUIRED(VERSION 3.14)  # FetchContent requires 3.11+, 3.14+ for better stability
PROJECT(subconverter LANGUAGES CXX)
SET(RELEASE_TARGET_NAME ${PROJECT_NAME})
SET(STATIC_TARGET_NAME ${PROJECT_NAME}_static)
SET(SUBCONVERTER_TARGETS)
SET(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/")
INCLUDE_DIRECTORIES("${CMAKE_SOURCE_DIR}/include/")

# ============================================================
# FetchContent Module for Auto-Downloading Dependencies
# ============================================================
INCLUDE(FetchContent)
INCLUDE(ExternalProject)

# Set download directory
SET(FETCHCONTENT_BASE_DIR "${CMAKE_BINARY_DIR}/_deps" CACHE PATH "FetchContent base directory")

# Option to control dependency download behavior
OPTION(AUTO_FETCH_DEPS "Automatically download missing dependencies using FetchContent" ON)
OPTION(FORCE_FETCH_DEPS "Force download all dependencies even if found on system" OFF)


if (MINGW)
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,--allow-multiple-definition")
endif()

IF(NOT CMAKE_BUILD_TYPE)
    SET(CMAKE_BUILD_TYPE Release)
ENDIF()
SET(CMAKE_CXX_STANDARD 20)

IF(NOT MSVC)
    ADD_COMPILE_OPTIONS(-Wall -Wextra -Wno-unused-parameter -Wno-unused-result)
ELSE()
    ADD_COMPILE_OPTIONS(/W4)
ENDIF()

#remove std::regex support since it is not compatible with group modifiers and slow
#OPTION(USING_STD_REGEX "Use std::regex from C++ library instead of PCRE2." OFF)
OPTION(USING_MALLOC_TRIM "Call malloc_trim after processing request to lower memory usage (Your system must support malloc_trim)." OFF)
#now using internal MD5 calculation
#OPTION(USING_MBEDTLS "Use mbedTLS instead of OpenSSL for MD5 calculation." OFF)
OPTION(BUILD_RELEASE_APP "Build full subconverter executable" ON)
OPTION(BUILD_STATIC_LIBRARY "Build a static library containing only the essential part." OFF)

INCLUDE(CheckCXXSourceCompiles)
CHECK_CXX_SOURCE_COMPILES(
"
#include<string>
int main(){std::to_string(0);}
" HAVE_TO_STRING)

# ============================================================
# Auto-Download Dependencies with FetchContent
# ============================================================

# ------------------------------------------------------------
# Rapidjson (Header-only library - no build needed)
# ------------------------------------------------------------
IF(FORCE_FETCH_DEPS OR (AUTO_FETCH_DEPS AND NOT RAPIDJSON_INCLUDE_DIRS))
    MESSAGE(STATUS "⬇️  Fetching RapidJSON from GitHub...")

    FetchContent_Declare(
        rapidjson
        GIT_REPOSITORY https://github.com/Tencent/rapidjson.git
        GIT_TAG        master
        GIT_SHALLOW    TRUE
        GIT_PROGRESS   TRUE
    )

    # Only download, don't configure/build (header-only library)
    FetchContent_GetProperties(rapidjson)
    IF(NOT rapidjson_POPULATED)
        FetchContent_Populate(rapidjson)
        SET(RAPIDJSON_INCLUDE_DIRS ${rapidjson_SOURCE_DIR}/include)
    ENDIF()

    MESSAGE(STATUS "✅ RapidJSON fetched successfully")
ENDIF()

# ------------------------------------------------------------
# toml11 (Header-only library - no build needed)
# ------------------------------------------------------------
IF(FORCE_FETCH_DEPS OR (AUTO_FETCH_DEPS AND NOT TOML11_INCLUDE_DIRS))
    MESSAGE(STATUS "⬇️  Fetching toml11 from GitHub...")

    FetchContent_Declare(
        toml11
        GIT_REPOSITORY https://github.com/ToruNiina/toml11.git
        GIT_TAG        v4.3.0
        GIT_SHALLOW    TRUE
        GIT_PROGRESS   TRUE
    )

    # Only download, don't configure/build (header-only library)
    FetchContent_GetProperties(toml11)
    IF(NOT toml11_POPULATED)
        FetchContent_Populate(toml11)
        SET(TOML11_INCLUDE_DIRS ${toml11_SOURCE_DIR}/include)
    ENDIF()

    MESSAGE(STATUS "✅ toml11 fetched successfully")
ENDIF()

# ------------------------------------------------------------
# yaml-cpp
# ------------------------------------------------------------
IF(NOT FORCE_FETCH_DEPS)
    FIND_PACKAGE(PkgConfig QUIET)
    IF(PKG_CONFIG_FOUND)
        PKG_CHECK_MODULES(YAML_CPP yaml-cpp QUIET)
    ENDIF()
ENDIF()

IF(FORCE_FETCH_DEPS OR (AUTO_FETCH_DEPS AND NOT YAML_CPP_FOUND))
    MESSAGE(STATUS "⬇️  Fetching yaml-cpp from GitHub...")

    FetchContent_Declare(
        yaml-cpp
        GIT_REPOSITORY https://github.com/jbeder/yaml-cpp.git
        GIT_TAG        0.8.0
        GIT_SHALLOW    TRUE
        GIT_PROGRESS   TRUE
    )

    # Configure yaml-cpp build options
    SET(YAML_CPP_BUILD_TESTS OFF CACHE INTERNAL "")
    SET(YAML_CPP_BUILD_TOOLS OFF CACHE INTERNAL "")
    SET(YAML_BUILD_SHARED_LIBS OFF CACHE INTERNAL "")
    SET(YAML_CPP_INSTALL OFF CACHE INTERNAL "")

    FetchContent_MakeAvailable(yaml-cpp)
    MESSAGE(STATUS "✅ yaml-cpp fetched and configured successfully")
    SET(YAML_CPP_LIBRARIES yaml-cpp)
ELSE()
    MESSAGE(STATUS "✅ Using system yaml-cpp")
    SET(YAML_CPP_LIBRARIES yaml-cpp)
ENDIF()

# ------------------------------------------------------------
# PCRE2
# ------------------------------------------------------------
IF(NOT FORCE_FETCH_DEPS)
    FIND_PACKAGE(PkgConfig QUIET)
    IF(PKG_CONFIG_FOUND)
        PKG_CHECK_MODULES(PCRE2 libpcre2-8 QUIET)
    ENDIF()
ENDIF()

IF(FORCE_FETCH_DEPS OR (AUTO_FETCH_DEPS AND NOT PCRE2_FOUND))
    MESSAGE(STATUS "⬇️  Fetching PCRE2 from GitHub...")

    FetchContent_Declare(
        pcre2
        GIT_REPOSITORY https://github.com/PCRE2Project/pcre2.git
        GIT_TAG        pcre2-10.44
        GIT_SHALLOW    TRUE
        GIT_PROGRESS   TRUE
    )

    # Configure PCRE2 build options
    SET(PCRE2_BUILD_TESTS OFF CACHE INTERNAL "")
    SET(PCRE2_BUILD_PCRE2GREP OFF CACHE INTERNAL "")
    SET(PCRE2_BUILD_PCRE2_16 OFF CACHE INTERNAL "")
    SET(PCRE2_BUILD_PCRE2_32 OFF CACHE INTERNAL "")
    SET(PCRE2_SUPPORT_JIT ON CACHE INTERNAL "")
    SET(BUILD_SHARED_LIBS OFF CACHE INTERNAL "")

    FetchContent_MakeAvailable(pcre2)
    MESSAGE(STATUS "✅ PCRE2 fetched and configured successfully")
    SET(PCRE2_LIBRARY pcre2-8-static)
ELSE()
    MESSAGE(STATUS "✅ Using system PCRE2")
    # Create interface library for system PCRE2
    IF(NOT TARGET pcre2-8-static)
        ADD_LIBRARY(pcre2-8-static INTERFACE)
        TARGET_INCLUDE_DIRECTORIES(pcre2-8-static INTERFACE ${PCRE2_INCLUDE_DIRS})
        TARGET_LINK_LIBRARIES(pcre2-8-static INTERFACE ${PCRE2_LIBRARIES})
    ENDIF()
    SET(PCRE2_LIBRARY pcre2-8-static)
ENDIF()

# ------------------------------------------------------------
# QuickJS (for BUILD_RELEASE_APP) - Built with Makefile
# ------------------------------------------------------------
IF(BUILD_RELEASE_APP)
    IF(NOT FORCE_FETCH_DEPS)
        FIND_PACKAGE(QuickJS QUIET)
    ENDIF()

    IF(FORCE_FETCH_DEPS OR (AUTO_FETCH_DEPS AND NOT QuickJS_FOUND))
        MESSAGE(STATUS "⬇️  Fetching QuickJS from GitHub...")

        SET(QUICKJS_PREFIX ${CMAKE_BINARY_DIR}/_deps/quickjs)
        SET(QUICKJS_INSTALL_DIR ${QUICKJS_PREFIX}/install)

        # Detect make command
        FIND_PROGRAM(MAKE_EXECUTABLE NAMES gmake make mingw32-make)
        IF(NOT MAKE_EXECUTABLE)
            MESSAGE(FATAL_ERROR "Make command not found! Please install make.")
        ENDIF()

        ExternalProject_Add(
            quickjs_external
            GIT_REPOSITORY https://github.com/bellard/quickjs.git
            GIT_TAG        master
            GIT_SHALLOW    TRUE
            PREFIX         ${QUICKJS_PREFIX}
            CONFIGURE_COMMAND ""
            BUILD_COMMAND ${MAKE_EXECUTABLE} -C <SOURCE_DIR> libquickjs.a
            BUILD_IN_SOURCE TRUE
            INSTALL_COMMAND ${CMAKE_COMMAND} -E make_directory ${QUICKJS_INSTALL_DIR}/lib
                    COMMAND ${CMAKE_COMMAND} -E make_directory ${QUICKJS_INSTALL_DIR}/include/quickjs
                    COMMAND ${CMAKE_COMMAND} -E copy <SOURCE_DIR>/libquickjs.a ${QUICKJS_INSTALL_DIR}/lib/
                    COMMAND ${CMAKE_COMMAND} -E copy <SOURCE_DIR>/quickjs.h ${QUICKJS_INSTALL_DIR}/include/quickjs/
                    COMMAND ${CMAKE_COMMAND} -E copy <SOURCE_DIR>/quickjs-libc.h ${QUICKJS_INSTALL_DIR}/include/quickjs/
            BUILD_BYPRODUCTS ${QUICKJS_INSTALL_DIR}/lib/libquickjs.a
            LOG_DOWNLOAD TRUE
            LOG_BUILD TRUE
        )

        # Create imported target
        ADD_LIBRARY(quickjs_lib STATIC IMPORTED)
        SET_TARGET_PROPERTIES(quickjs_lib PROPERTIES
            IMPORTED_LOCATION ${QUICKJS_INSTALL_DIR}/lib/libquickjs.a
        )
        ADD_DEPENDENCIES(quickjs_lib quickjs_external)

        SET(QUICKJS_INCLUDE_DIRS ${QUICKJS_INSTALL_DIR}/include)
        SET(QUICKJS_LIBRARIES quickjs_lib)
        SET(QuickJS_FOUND TRUE)

        MESSAGE(STATUS "✅ QuickJS will be built from source")
    ELSEIF(QuickJS_FOUND)
        MESSAGE(STATUS "✅ Using system QuickJS")
    ENDIF()
ENDIF()

# ------------------------------------------------------------
# LibCron (for BUILD_RELEASE_APP) - CMake-based project
# ------------------------------------------------------------
IF(BUILD_RELEASE_APP)
    IF(NOT FORCE_FETCH_DEPS)
        FIND_PACKAGE(LibCron QUIET)
    ENDIF()

    IF(FORCE_FETCH_DEPS OR (AUTO_FETCH_DEPS AND NOT LibCron_FOUND))
        MESSAGE(STATUS "⬇️  Fetching LibCron from GitHub...")

        FetchContent_Declare(
            libcron
            GIT_REPOSITORY https://github.com/PerMalmberg/libcron.git
            GIT_TAG        master
            GIT_SHALLOW    TRUE
            GIT_PROGRESS   TRUE
        )

        # Configure libcron build options
        SET(LIBCRON_BUILD_TESTS OFF CACHE INTERNAL "")
        SET(LIBCRON_BUILD_EXAMPLES OFF CACHE INTERNAL "")

        FetchContent_MakeAvailable(libcron)

        # Set variables for linking
        SET(LIBCRON_INCLUDE_DIRS ${libcron_SOURCE_DIR}/libcron/include)
        SET(LIBCRON_LIBRARIES libcron)
        SET(LibCron_FOUND TRUE)

        MESSAGE(STATUS "✅ LibCron fetched and configured successfully")
    ELSEIF(LibCron_FOUND)
        MESSAGE(STATUS "✅ Using system LibCron")
    ENDIF()
ENDIF()

# ------------------------------------------------------------
# CURL (for BUILD_RELEASE_APP and BUILD_STATIC_LIBRARY)
# ------------------------------------------------------------
IF(BUILD_RELEASE_APP OR BUILD_STATIC_LIBRARY)
    IF(NOT FORCE_FETCH_DEPS)
        FIND_PACKAGE(CURL 7.54.0 QUIET)
    ENDIF()

    IF(FORCE_FETCH_DEPS OR (AUTO_FETCH_DEPS AND NOT CURL_FOUND))
        MESSAGE(STATUS "⬇️  Fetching CURL from GitHub...")

        FetchContent_Declare(
            curl
            GIT_REPOSITORY https://github.com/curl/curl.git
            GIT_TAG        curl-8_5_0
            GIT_SHALLOW    TRUE
            GIT_PROGRESS   TRUE
        )

        # Configure CURL build options
        SET(BUILD_CURL_EXE OFF CACHE INTERNAL "")
        SET(BUILD_SHARED_LIBS OFF CACHE INTERNAL "")
        SET(CURL_STATICLIB ON CACHE INTERNAL "")
        SET(HTTP_ONLY ON CACHE INTERNAL "")
        SET(BUILD_TESTING OFF CACHE INTERNAL "")
        SET(CURL_USE_OPENSSL OFF CACHE INTERNAL "")
        SET(CURL_USE_LIBSSH2 OFF CACHE INTERNAL "")
        SET(CURL_DISABLE_INSTALL OFF CACHE INTERNAL "")
        SET(CURL_DISABLE_HEADERS OFF CACHE INTERNAL "")

        FetchContent_MakeAvailable(curl)

        # Set variables for consistent usage
        SET(CURL_INCLUDE_DIRS ${curl_SOURCE_DIR}/include)
        IF(TARGET libcurl_static)
            SET(CURL_LIBRARY libcurl_static)
            SET(CURL_LIBRARIES libcurl_static)
        ELSEIF(TARGET curl_static)
            SET(CURL_LIBRARY curl_static)
            SET(CURL_LIBRARIES curl_static)
        ELSEIF(TARGET libcurl)
            SET(CURL_LIBRARY libcurl)
            SET(CURL_LIBRARIES libcurl)
        ELSE()
            SET(CURL_LIBRARY libcurl)
            SET(CURL_LIBRARIES libcurl)
        ENDIF()

        MESSAGE(STATUS "✅ CURL fetched and configured successfully")
        MESSAGE(STATUS "   Include dirs: ${CURL_INCLUDE_DIRS}")
        MESSAGE(STATUS "   Library: ${CURL_LIBRARY}")
    ELSE()
        MESSAGE(STATUS "✅ Using system CURL")
        IF(CURL_FOUND AND NOT BUILD_STATIC_LIBRARY)
            SET(CURL_INCLUDE_DIRS ${CURL_INCLUDE_DIR})
            SET(CURL_LIBRARIES CURL::libcurl)
        ENDIF()
    ENDIF()
ENDIF()

IF(BUILD_RELEASE_APP)

ADD_EXECUTABLE(${RELEASE_TARGET_NAME} 
    src/generator/config/nodemanip.cpp
    src/generator/config/ruleconvert.cpp
    src/generator/config/subexport.cpp
    src/generator/template/templates.cpp
    src/handler/interfaces.cpp
    src/handler/multithread.cpp
    src/handler/upload.cpp
    src/handler/webget.cpp
    src/handler/settings.cpp
    src/main.cpp
    src/parser/infoparser.cpp
    src/parser/subparser.cpp
    src/script/cron.cpp
    src/script/script_quickjs.cpp
#    src/server/webserver_libevent.cpp
    src/server/webserver_httplib.cpp
    src/utils/base64/base64.cpp
    src/utils/codepage.cpp
    src/utils/file.cpp
    src/utils/logger.cpp
    src/utils/md5/md5.cpp
    src/utils/network.cpp
    src/utils/regexp.cpp
    src/utils/string.cpp
    src/utils/system.cpp
    src/utils/urlencode.cpp)
LIST(APPEND SUBCONVERTER_TARGETS ${RELEASE_TARGET_NAME})
TARGET_INCLUDE_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE src)
TARGET_LINK_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${CMAKE_SOURCE_DIR})

FIND_PACKAGE(PkgConfig REQUIRED)

SET(THREADS_PREFER_PTHREAD_FLAG ON)
FIND_PACKAGE(Threads REQUIRED)
TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} ${CMAKE_THREAD_LIBS_INIT})

#PKG_CHECK_MODULES(LIBEVENT libevent>=2.1.10 REQUIRED)
#FIND_PATH(LIBEVENT_INCLUDE_DIR NAMES event.h PATHS ${LIBEVENT_INCLUDE_DIRS})
#FIND_LIBRARY(LIBEVENT_LIBRARY NAMES event PATHS ${LIBEVENT_LIBRARY_DIRS})
#TARGET_LINK_DIRECTORIES(${BUILD_TARGET_NAME} PRIVATE ${LIBEVENT_LIBRARY_DIRS})
#TARGET_INCLUDE_DIRECTORIES(${BUILD_TARGET_NAME} PRIVATE ${LIBEVENT_INCLUDE_DIR})
#TARGET_LINK_LIBRARIES(${BUILD_TARGET_NAME} ${LIBEVENT_LIBRARY})

# CURL - Already handled by FetchContent above
IF(CURL_FOUND OR TARGET CURL::libcurl)
    TARGET_LINK_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${CURL_LIBRARY_DIRS})
    TARGET_INCLUDE_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${CURL_INCLUDE_DIRS})
    TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} CURL::libcurl)
    TARGET_COMPILE_DEFINITIONS(${RELEASE_TARGET_NAME} PRIVATE -DCURL_STATICLIB)
ELSEIF(CURL_LIBRARIES)
    # Use fetched CURL
    TARGET_INCLUDE_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${CURL_INCLUDE_DIRS})
    TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} ${CURL_LIBRARIES})
    TARGET_COMPILE_DEFINITIONS(${RELEASE_TARGET_NAME} PRIVATE -DCURL_STATICLIB)
ELSE()
    MESSAGE(WARNING "CURL not found - some features may not work")
ENDIF()

# RapidJSON - Already handled by FetchContent above
TARGET_INCLUDE_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${RAPIDJSON_INCLUDE_DIRS})

# toml11 - Already handled by FetchContent above
TARGET_INCLUDE_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${TOML11_INCLUDE_DIRS})

# yaml-cpp - Already handled by FetchContent above
TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} ${YAML_CPP_LIBRARIES})
TARGET_COMPILE_DEFINITIONS(${RELEASE_TARGET_NAME} PRIVATE -DYAML_CPP_STATIC_DEFINE)

# PCRE2 - Already handled by FetchContent above
TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} ${PCRE2_LIBRARY})
TARGET_COMPILE_DEFINITIONS(${RELEASE_TARGET_NAME} PRIVATE -DPCRE2_STATIC)

# QuickJS - Already handled by FetchContent/ExternalProject above
IF(QuickJS_FOUND)
    TARGET_INCLUDE_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${QUICKJS_INCLUDE_DIRS})
    TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} ${QUICKJS_LIBRARIES})

    # Add dependency on ExternalProject if using downloaded QuickJS
    IF(TARGET quickjs_external)
        ADD_DEPENDENCIES(${RELEASE_TARGET_NAME} quickjs_external)
    ENDIF()
ELSE()
    MESSAGE(FATAL_ERROR "QuickJS not found! Please install it or enable AUTO_FETCH_DEPS")
ENDIF()

# LibCron - Already handled by FetchContent above
IF(LibCron_FOUND)
    TARGET_INCLUDE_DIRECTORIES(${RELEASE_TARGET_NAME} PRIVATE ${LIBCRON_INCLUDE_DIRS})
    TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} ${LIBCRON_LIBRARIES})
ELSE()
    MESSAGE(FATAL_ERROR "LibCron not found! Please install it or enable AUTO_FETCH_DEPS")
ENDIF()

IF(WIN32)
    TARGET_LINK_LIBRARIES(${RELEASE_TARGET_NAME} wsock32 ws2_32)
ELSE()
    INCLUDE(GNUInstallDirs)
    INSTALL(TARGETS ${RELEASE_TARGET_NAME} DESTINATION ${CMAKE_INSTALL_BINDIR}/${RELEASE_TARGET_NAME})
    INSTALL(DIRECTORY base/ DESTINATION ${CMAKE_INSTALL_BINDIR}/${RELEASE_TARGET_NAME} FILES_MATCHING PATTERN "*")
ENDIF()

ENDIF() #BUILD_RELEASE_APP

IF(BUILD_STATIC_LIBRARY)

ADD_LIBRARY(${STATIC_TARGET_NAME} STATIC
    src/generator/config/ruleconvert.cpp
    src/generator/config/subexport.cpp
    src/generator/template/templates.cpp
    src/lib/wrapper.cpp
    src/lib/node_export.cpp
    src/parser/subparser.cpp
    src/utils/base64/base64.cpp
    src/utils/codepage.cpp
    src/utils/logger.cpp
    src/utils/md5/md5.cpp
    src/utils/network.cpp
    src/utils/regexp.cpp
    src/utils/string.cpp
    src/utils/urlencode.cpp)
LIST(APPEND SUBCONVERTER_TARGETS ${STATIC_TARGET_NAME})
TARGET_COMPILE_DEFINITIONS(${STATIC_TARGET_NAME} PRIVATE -DNO_JS_RUNTIME -DNO_WEBGET)

TARGET_INCLUDE_DIRECTORIES(${STATIC_TARGET_NAME} PUBLIC src)

# RapidJSON - Already handled by FetchContent above
TARGET_INCLUDE_DIRECTORIES(${STATIC_TARGET_NAME} PRIVATE ${RAPIDJSON_INCLUDE_DIRS})

# toml11 - Already handled by FetchContent above
TARGET_INCLUDE_DIRECTORIES(${STATIC_TARGET_NAME} PRIVATE ${TOML11_INCLUDE_DIRS})

FIND_PACKAGE(PkgConfig REQUIRED)

# yaml-cpp - Already handled by FetchContent above
TARGET_LINK_LIBRARIES(${STATIC_TARGET_NAME} PRIVATE ${YAML_CPP_LIBRARIES})
TARGET_COMPILE_DEFINITIONS(${STATIC_TARGET_NAME} PRIVATE -DYAML_CPP_STATIC_DEFINE)

# PCRE2 - Already handled by FetchContent above
TARGET_LINK_LIBRARIES(${STATIC_TARGET_NAME} PRIVATE ${PCRE2_LIBRARY})
TARGET_COMPILE_DEFINITIONS(${STATIC_TARGET_NAME} PRIVATE -DPCRE2_STATIC)

# CURL - Include headers for static library build (needed by templates.cpp)
IF(CURL_LIBRARIES)
    TARGET_INCLUDE_DIRECTORIES(${STATIC_TARGET_NAME} PRIVATE ${CURL_INCLUDE_DIRS})
    TARGET_LINK_LIBRARIES(${STATIC_TARGET_NAME} PRIVATE ${CURL_LIBRARIES})
    TARGET_COMPILE_DEFINITIONS(${STATIC_TARGET_NAME} PRIVATE -DCURL_STATICLIB)
ENDIF()

IF(WIN32)
    TARGET_LINK_LIBRARIES(${STATIC_TARGET_NAME} PRIVATE ws2_32)
ENDIF()

ENDIF() #BUILD_STATIC_LIBRARY

# ============================================================
# Full Static Library (Bundle all dependencies into one .a)
# Similar to Makefile's "full-static" target
# ============================================================

# Option to build bundled static library
OPTION(BUILD_FULL_STATIC "Build full static library bundling all dependencies" ON)

IF(BUILD_STATIC_LIBRARY AND BUILD_FULL_STATIC)

    SET(FULL_STATIC_TARGET_NAME ${STATIC_TARGET_NAME}_full)
    SET(FULL_STATIC_LIB ${CMAKE_BINARY_DIR}/lib${FULL_STATIC_TARGET_NAME}.a)

    MESSAGE(STATUS "🔨 Full static library will be built: ${FULL_STATIC_LIB}")

    IF(UNIX AND NOT APPLE)
        # Linux: Use ar with MRI (Multi-library Resource Interchange) script

        # Determine dependencies to bundle
        SET(BUNDLE_DEPS ${STATIC_TARGET_NAME} yaml-cpp)

        # Check if PCRE2 is a fetchable static library (not system INTERFACE library)
        IF(TARGET pcre2-8-static)
            GET_TARGET_PROPERTY(PCRE2_TYPE pcre2-8-static TYPE)
            IF(NOT PCRE2_TYPE STREQUAL "INTERFACE_LIBRARY")
                LIST(APPEND BUNDLE_DEPS pcre2-8-static)
                MESSAGE(STATUS "   ✅ PCRE2 will be included in full static library")
            ELSE()
                MESSAGE(STATUS "   ⚠️  PCRE2 is system library (INTERFACE), use FORCE_FETCH_DEPS=ON to include it")
            ENDIF()
        ENDIF()

        ADD_CUSTOM_TARGET(${FULL_STATIC_TARGET_NAME} ALL
            COMMAND ${CMAKE_COMMAND} -E echo "🔧 Creating full static library bundle..."
            COMMAND ${CMAKE_COMMAND} -E remove -f ${FULL_STATIC_LIB}
            COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_BINARY_DIR}/bundle.mri

            # Generate MRI script header
            COMMAND ${CMAKE_COMMAND} -E echo "CREATE ${FULL_STATIC_LIB}" > ${CMAKE_BINARY_DIR}/bundle.mri

            # Add subconverter static library
            COMMAND ${CMAKE_COMMAND} -E echo "ADDLIB $<TARGET_FILE:${STATIC_TARGET_NAME}>" >> ${CMAKE_BINARY_DIR}/bundle.mri

            # Add yaml-cpp
            COMMAND ${CMAKE_COMMAND} -E echo "ADDLIB $<TARGET_FILE:yaml-cpp>" >> ${CMAKE_BINARY_DIR}/bundle.mri

            # Add PCRE2 if it's a real static library
            COMMAND ${CMAKE_COMMAND} -E echo "$<$<AND:$<TARGET_EXISTS:pcre2-8-static>,$<NOT:$<STREQUAL:$<TARGET_PROPERTY:pcre2-8-static,TYPE>,INTERFACE_LIBRARY>>>:ADDLIB $<TARGET_FILE:pcre2-8-static>>" >> ${CMAKE_BINARY_DIR}/bundle.mri

            # MRI script footer
            COMMAND ${CMAKE_COMMAND} -E echo "SAVE" >> ${CMAKE_BINARY_DIR}/bundle.mri
            COMMAND ${CMAKE_COMMAND} -E echo "END" >> ${CMAKE_BINARY_DIR}/bundle.mri

            # Execute ar with MRI script
            COMMAND ar -M < ${CMAKE_BINARY_DIR}/bundle.mri

            # Verify the library
            COMMAND ${CMAKE_COMMAND} -E echo "✅ Full static library created successfully!"
            COMMAND ${CMAKE_COMMAND} -E echo "   Location: ${FULL_STATIC_LIB}"

            DEPENDS ${BUNDLE_DEPS}
            BYPRODUCTS ${FULL_STATIC_LIB}
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
            COMMENT "📦 Bundling ${STATIC_TARGET_NAME} with all dependencies"
        )

    ELSEIF(APPLE)
        # macOS: Use libtool -static

        # Determine dependencies to bundle
        SET(BUNDLE_DEPS ${STATIC_TARGET_NAME} yaml-cpp)
        SET(BUNDLE_LIBS $<TARGET_FILE:${STATIC_TARGET_NAME}> $<TARGET_FILE:yaml-cpp>)

        # Check if PCRE2 is a real static library
        IF(TARGET pcre2-8-static)
            GET_TARGET_PROPERTY(PCRE2_TYPE pcre2-8-static TYPE)
            IF(NOT PCRE2_TYPE STREQUAL "INTERFACE_LIBRARY")
                LIST(APPEND BUNDLE_DEPS pcre2-8-static)
                SET(BUNDLE_LIBS ${BUNDLE_LIBS} $<TARGET_FILE:pcre2-8-static>)
                MESSAGE(STATUS "   ✅ PCRE2 will be included in full static library")
            ELSE()
                MESSAGE(STATUS "   ⚠️  PCRE2 is system library (INTERFACE), use FORCE_FETCH_DEPS=ON to include it")
            ENDIF()
        ENDIF()

        ADD_CUSTOM_TARGET(${FULL_STATIC_TARGET_NAME} ALL
            COMMAND ${CMAKE_COMMAND} -E echo "🔧 Creating full static library for macOS..."
            COMMAND libtool -static -o ${FULL_STATIC_LIB} ${BUNDLE_LIBS}
            COMMAND ${CMAKE_COMMAND} -E echo "✅ Full static library created: ${FULL_STATIC_LIB}"
            DEPENDS ${BUNDLE_DEPS}
            BYPRODUCTS ${FULL_STATIC_LIB}
            COMMENT "📦 Bundling ${STATIC_TARGET_NAME} with all dependencies"
        )

    ELSEIF(MSVC OR MINGW)
        # Windows: Use lib.exe or ar
        SET(FULL_STATIC_LIB ${CMAKE_BINARY_DIR}/${FULL_STATIC_TARGET_NAME}.lib)

        # Determine dependencies to bundle
        SET(BUNDLE_DEPS ${STATIC_TARGET_NAME} yaml-cpp)
        SET(BUNDLE_LIBS $<TARGET_FILE:${STATIC_TARGET_NAME}> $<TARGET_FILE:yaml-cpp>)

        # Check if PCRE2 is a real static library
        IF(TARGET pcre2-8-static)
            GET_TARGET_PROPERTY(PCRE2_TYPE pcre2-8-static TYPE)
            IF(NOT PCRE2_TYPE STREQUAL "INTERFACE_LIBRARY")
                LIST(APPEND BUNDLE_DEPS pcre2-8-static)
                SET(BUNDLE_LIBS ${BUNDLE_LIBS} $<TARGET_FILE:pcre2-8-static>)
                MESSAGE(STATUS "   ✅ PCRE2 will be included in full static library")
            ELSE()
                MESSAGE(STATUS "   ⚠️  PCRE2 is system library (INTERFACE), use FORCE_FETCH_DEPS=ON to include it")
            ENDIF()
        ENDIF()

        IF(MSVC)
            ADD_CUSTOM_TARGET(${FULL_STATIC_TARGET_NAME} ALL
                COMMAND ${CMAKE_COMMAND} -E echo "🔧 Creating full static library for Windows (MSVC)..."
                COMMAND lib.exe /OUT:${FULL_STATIC_LIB} ${BUNDLE_LIBS}
                COMMAND ${CMAKE_COMMAND} -E echo "✅ Full static library created: ${FULL_STATIC_LIB}"
                DEPENDS ${BUNDLE_DEPS}
                BYPRODUCTS ${FULL_STATIC_LIB}
                COMMENT "📦 Bundling ${STATIC_TARGET_NAME} with all dependencies"
            )
        ELSE()
            # MinGW uses ar
            ADD_CUSTOM_TARGET(${FULL_STATIC_TARGET_NAME} ALL
                COMMAND ${CMAKE_COMMAND} -E echo "🔧 Creating full static library for Windows (MinGW)..."
                COMMAND ${CMAKE_COMMAND} -E echo "CREATE ${FULL_STATIC_LIB}" > ${CMAKE_BINARY_DIR}/bundle.mri
                COMMAND ${CMAKE_COMMAND} -E echo "ADDLIB $<TARGET_FILE:${STATIC_TARGET_NAME}>" >> ${CMAKE_BINARY_DIR}/bundle.mri
                COMMAND ${CMAKE_COMMAND} -E echo "ADDLIB $<TARGET_FILE:yaml-cpp>" >> ${CMAKE_BINARY_DIR}/bundle.mri
                COMMAND ${CMAKE_COMMAND} -E echo "$<$<AND:$<TARGET_EXISTS:pcre2-8-static>,$<NOT:$<STREQUAL:$<TARGET_PROPERTY:pcre2-8-static,TYPE>,INTERFACE_LIBRARY>>>:ADDLIB $<TARGET_FILE:pcre2-8-static>>" >> ${CMAKE_BINARY_DIR}/bundle.mri
                COMMAND ${CMAKE_COMMAND} -E echo "SAVE" >> ${CMAKE_BINARY_DIR}/bundle.mri
                COMMAND ${CMAKE_COMMAND} -E echo "END" >> ${CMAKE_BINARY_DIR}/bundle.mri
                COMMAND ar -M < ${CMAKE_BINARY_DIR}/bundle.mri
                COMMAND ${CMAKE_COMMAND} -E echo "✅ Full static library created: ${FULL_STATIC_LIB}"
                DEPENDS ${BUNDLE_DEPS}
                BYPRODUCTS ${FULL_STATIC_LIB}
                COMMENT "📦 Bundling ${STATIC_TARGET_NAME} with all dependencies"
            )
        ENDIF()
    ENDIF()

ENDIF() # BUILD_STATIC_LIBRARY AND BUILD_FULL_STATIC

IF(SUBCONVERTER_TARGETS)
    IF(HAVE_TO_STRING)
        FOREACH(TGT ${SUBCONVERTER_TARGETS})
            TARGET_COMPILE_DEFINITIONS(${TGT} PRIVATE -DHAVE_TO_STRING)
        ENDFOREACH()
    ENDIF()

    IF(USING_MALLOC_TRIM)
        FOREACH(TGT ${SUBCONVERTER_TARGETS})
            TARGET_COMPILE_DEFINITIONS(${TGT} PRIVATE -DMALLOC_TRIM)
        ENDFOREACH()
    ENDIF()
ENDIF()
