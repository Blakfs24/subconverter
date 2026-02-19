# Native static SDK releases

`.github/workflows/native-libraries.yml` builds Android (armeabi-v7a, arm64-v8a,
x86_64), macOS (amd64, arm64), Linux amd64 glibc, and Windows amd64 MinGW SDKs.
iOS is excluded. Existing standalone executable, Docker, and Alpine static
workflows remain available; they exclude `v*` tags so they do not
publish conflicting releases.

After committing the SDK changes, publish a fixed version with a tag:

```sh
git tag v1.0.0
git push origin v1.0.0
```

Every build must succeed before the release is assembled and published. Branch
and pull request builds upload the same SDK format as Actions artifacts but do
not publish a Release. Do not replace an existing release's SDK files; publish
a new version for a different build.

Each `subconverter-<target>.tar.gz` contains:

```text
lib/libsubconverter.a
include/node_export.h
manifest.json
LICENSE
```

The library bundles subconverter, yaml-cpp, PCRE2 and curl. It is a static
archive intended for linking into another library or executable. System
libraries and the C++ runtime remain the consumer's responsibility.

`manifest.json` records target, source commit, C ABI version, PIC, compiler and
platform requirements, plus file hashes. `subconverter-index.json` contains
all seven archive checksums, manifest checksums and manifests. Consumers pin
that index in their own repository rather than downloading `latest` on every
build. `SHA256SUMS` is also published for manual downloads.

Build contracts are defined in `scripts/native-targets.json`. Android uses the
official NDK CMake toolchain, fixed NDK 28.2.13676358 and `c++_shared`; macOS sets
its deployment target to 13.0. Windows uses MinGW GCC instead of the separate
legacy Zig workflow, so consumers can match GCC and libstdc++ consistently.
Linux uses the Ubuntu 22.04/glibc 2.35 baseline.

Local example (requires CMake 3.20+, Ninja and the platform toolchain):

```sh
python3 scripts/build-native.py --target macos-amd64
python3 scripts/package-native.py package --target macos-amd64 --version v1.0.0
```

The build script requests CMake File API toolchain metadata before configuring.
Packaging uses the effective CXX compiler reported by CMake, including Android
NDK settings that are not stored in `CMakeCache.txt`. Reconfigure existing
Android build directories with `build-native.py` before packaging them.

For Android, set `ANDROID_NDK` to the fixed NDK first. Use a separate build
directory for each target when invoking the script repeatedly:

```sh
python3 scripts/build-native.py --target android-arm64 --build-dir build/android-arm64
python3 scripts/package-native.py package --target android-arm64 \
  --build-dir build/android-arm64 --version v1.0.0
```

The `index` operation requires archives and sidecars for all seven targets in
one output directory. `singtools` imports the resulting published index using:

```sh
dart tool/subconverter.dart lock --version v1.0.0
```
