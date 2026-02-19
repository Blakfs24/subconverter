"""Package static SDKs and generate a versioned release index for consumers."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "scripts/native-targets.json").read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def cache_values(build):
    values = {}
    for line in (build / "CMakeCache.txt").read_text().splitlines():
        match = re.match(r"([^:#]+):[^=]+=(.*)", line)
        if match:
            values[match[1]] = match[2]
    return values


def compiler_path(build, cache):
    reply = build / ".cmake/api/v1/reply"
    indexes = sorted(reply.glob("index-*.json"))
    if indexes:
        index = json.loads(indexes[-1].read_text())
        response = index.get("reply", {}).get("client-subconverter", {}).get("toolchains-v1")
        if response is not None:
            if "error" in response:
                raise ValueError(f"CMake toolchain metadata unavailable: {response['error']}. Use CMake 3.20 or newer.")
            toolchains = json.loads((reply / response["jsonFile"]).read_text())
            for toolchain in toolchains["toolchains"]:
                if toolchain["language"] == "CXX" and toolchain.get("compiler", {}).get("path"):
                    return toolchain["compiler"]["path"]
            raise ValueError("CMake toolchain metadata does not contain a CXX compiler")
    # Keep packaging previously configured desktop build directories possible.
    # Do not guess a host compiler when an NDK build has no cached compiler.
    if cache.get("CMAKE_CXX_COMPILER"):
        return cache["CMAKE_CXX_COMPILER"]
    raise ValueError("CXX compiler metadata is missing. Reconfigure with scripts/build-native.py before packaging.")


def package(target, build, output, version, repository):
    spec = dict(CONFIG["targets"][target])
    cache = cache_values(build)
    if cache.get("BUILD_WITH_PIC") != "ON" or cache.get("BUILD_RELEASE_APP") != "OFF":
        raise ValueError("SDK builds require BUILD_WITH_PIC=ON and BUILD_RELEASE_APP=OFF")
    compiler = compiler_path(build, cache)
    toolchain = {"cxx": command(compiler, "--version").splitlines()[0]}
    if spec["os"] == "android":
        ndk_path = cache.get("CMAKE_ANDROID_NDK") or cache.get("ANDROID_NDK")
        # Official NDK toolchain variables are not all guaranteed cache entries.
        ndk = Path(ndk_path) if ndk_path else Path(cache["CMAKE_TOOLCHAIN_FILE"]).resolve().parents[2]
        properties = (ndk / "source.properties").read_text()
        revision = re.search(r"Pkg.Revision\s*=\s*(\S+)", properties)[1]
        if revision != CONFIG["ndk_version"]:
            raise ValueError(f"NDK mismatch: expected {CONFIG['ndk_version']}, got {revision}")
        if cache.get("ANDROID_ABI") != spec["android_abi"] or cache.get("ANDROID_STL") != "c++_shared":
            raise ValueError("Android ABI/STL does not match the SDK target")
        if cache.get("ANDROID_PLATFORM") != f"android-{spec['android_api']}":
            raise ValueError("Android API does not match the SDK target")
        spec["ndk_version"] = revision
    if spec["os"] == "darwin":
        if cache.get("CMAKE_OSX_DEPLOYMENT_TARGET") != spec["deployment_target"]:
            raise ValueError("macOS deployment target mismatch")
        arch = "x86_64" if spec["arch"] == "amd64" else "arm64"
        if cache.get("CMAKE_OSX_ARCHITECTURES") != arch:
            raise ValueError("macOS architecture mismatch")
    if spec["os"] == "windows":
        triple = command(compiler, "-dumpmachine")
        if "x86_64" not in triple or "mingw" not in triple:
            raise ValueError("Windows SDK requires x86_64 MinGW GCC")
        toolchain["triple"] = triple
        toolchain["gcc_version"] = command(compiler, "-dumpfullversion")

    library = build / ("subconverter_static_full.lib" if spec["os"] == "windows" else "libsubconverter_static_full.a")
    output.mkdir(parents=True, exist_ok=True)
    asset = f"subconverter-{target}.tar.gz"
    with tempfile.TemporaryDirectory(prefix="subconverter-sdk-") as temporary:
        stage = Path(temporary)
        files = {
            "lib/libsubconverter.a": library,
            "include/node_export.h": ROOT / "src/lib/node_export.h",
            "LICENSE": ROOT / "LICENSE",
        }
        manifest = {
            "schema": 1, "version": version, "source_commit": command("git", "rev-parse", "HEAD"),
            "target": target, "abi": 1, "pic": True, **spec, "toolchain": toolchain,
            "files": {name: digest(path) for name, path in files.items()},
        }
        for name, source in files.items():
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        manifest_file = stage / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2) + "\n")
        archive = output / asset
        with tarfile.open(archive, "w:gz") as tar:
            for name in [*files, "manifest.json"]:
                tar.add(stage / name, arcname=name, recursive=False)
        entry = {
            "url": f"https://github.com/{repository}/releases/download/{version}/{asset}",
            "sha256": digest(archive), "manifest_sha256": digest(manifest_file), "manifest": manifest,
        }
    (output / f"{target}.json").write_text(json.dumps(entry, indent=2) + "\n")
    return archive


def index(directory, version, repository):
    artifacts = {}
    for target in CONFIG["targets"]:
        entry = json.loads((directory / f"{target}.json").read_text())
        manifest = entry["manifest"]
        archive = directory / f"subconverter-{target}.tar.gz"
        if manifest["target"] != target or manifest["version"] != version or digest(archive) != entry["sha256"]:
            raise ValueError(f"Mismatched SDK release entry: {target}")
        expected_url = f"https://github.com/{repository}/releases/download/{version}/{archive.name}"
        if entry["url"] != expected_url:
            raise ValueError(f"Unexpected release URL: {target}")
        artifacts[target] = entry
    commits = {entry["manifest"]["source_commit"] for entry in artifacts.values()}
    if len(commits) != 1:
        raise ValueError("All SDK targets must use the same source commit")
    document = {"schema": 1, "repository": repository, "version": version, "artifacts": artifacts}
    (directory / "subconverter-index.json").write_text(json.dumps(document, indent=2) + "\n")
    archives = sorted(directory.glob("subconverter-*.tar.gz"))
    (directory / "SHA256SUMS").write_text("".join(f"{digest(path)}  {path.name}\n" for path in archives))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["package", "index"])
    parser.add_argument("--target", choices=CONFIG["targets"])
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--version", default=os.environ.get("SDK_VERSION"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "Blakfs24/subconverter"))
    args = parser.parse_args()
    if not args.version or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", args.version):
        parser.error("--version must be a release tag or CI version")
    if args.operation == "package":
        if not args.target:
            parser.error("package requires --target")
        print(package(args.target, args.build_dir.resolve(), args.output, args.version, args.repository))
    else:
        index(args.output, args.version, args.repository)


if __name__ == "__main__":
    main()
