"""Build a release SDK with the platform contract in native-targets.json."""

import argparse
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "scripts/native-targets.json").read_text())


def request_toolchain_metadata(build):
    # File API reports effective compiler settings, including non-cache variables
    # set by the Android NDK toolchain. toolchains-v1 requires CMake 3.20+.
    query = build / ".cmake/api/v1/query/client-subconverter/toolchains-v1"
    query.parent.mkdir(parents=True, exist_ok=True)
    query.touch()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=CONFIG["targets"])
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    args = parser.parse_args()
    target = CONFIG["targets"][args.target]
    configure = [
        "cmake", "-S", str(ROOT), "-B", str(args.build_dir), "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_RELEASE_APP=OFF",
        "-DBUILD_STATIC_LIBRARY=ON", "-DBUILD_FULL_STATIC=ON", "-DBUILD_WITH_PIC=ON",
        "-DFORCE_FETCH_DEPS=ON", "-DAUTO_FETCH_DEPS=ON", "-DCMAKE_POLICY_VERSION_MINIMUM=3.15",
    ]
    if target["os"] == "android":
        ndk = os.environ.get("ANDROID_NDK") or os.environ.get("ANDROID_NDK_HOME")
        if not ndk:
            parser.error("ANDROID_NDK is required")
        configure += [
            f"-DCMAKE_TOOLCHAIN_FILE={ndk}/build/cmake/android.toolchain.cmake",
            f"-DANDROID_ABI={target['android_abi']}",
            f"-DANDROID_PLATFORM=android-{target['android_api']}", "-DANDROID_STL=c++_shared",
        ]
    elif target["os"] == "darwin":
        arch = "x86_64" if target["arch"] == "amd64" else "arm64"
        configure += [f"-DCMAKE_OSX_ARCHITECTURES={arch}", f"-DCMAKE_OSX_DEPLOYMENT_TARGET={target['deployment_target']}"]
    elif target["os"] == "windows":
        configure += ["-DCMAKE_C_COMPILER=gcc", "-DCMAKE_CXX_COMPILER=g++"]
    request_toolchain_metadata(args.build_dir)
    subprocess.run(configure, check=True)
    subprocess.run(["cmake", "--build", str(args.build_dir), "--target", "subconverter_static_full", "--parallel", "4"], check=True)


if __name__ == "__main__":
    main()
