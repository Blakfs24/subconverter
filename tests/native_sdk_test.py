import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("package_native", ROOT / "scripts/package-native.py")
SDK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SDK)
BUILD_SPEC = importlib.util.spec_from_file_location("build_native", ROOT / "scripts/build-native.py")
BUILD = importlib.util.module_from_spec(BUILD_SPEC)
BUILD_SPEC.loader.exec_module(BUILD)


class NativeSdkTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sdk-package-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.output = self.directory / "dist"
        self.version = "v1.0.0"
        self.repository = "Blakfs24/subconverter"
        self.command_patch = patch.object(SDK, "command", side_effect=self.command)
        self.command_mock = self.command_patch.start()
        self.addCleanup(self.command_patch.stop)

    def command(self, *args):
        if args[0] == "git":
            return "a" * 40
        if args[-1] == "-dumpmachine":
            return "x86_64-w64-mingw32"
        if args[-1] == "-dumpfullversion":
            return "13.2.0"
        return "fixture compiler"

    def package(self, target, overrides=None):
        spec = SDK.CONFIG["targets"][target]
        build = self.directory / target
        build.mkdir(exist_ok=True)
        cache = {"BUILD_WITH_PIC": "ON", "BUILD_RELEASE_APP": "OFF", "CMAKE_CXX_COMPILER": "fixture-cxx"}
        if spec["os"] == "android":
            ndk = self.directory / "ndk"
            ndk.mkdir(exist_ok=True)
            (ndk / "source.properties").write_text(f"Pkg.Revision = {SDK.CONFIG['ndk_version']}\n")
            cache.update({"CMAKE_ANDROID_NDK": str(ndk), "ANDROID_ABI": spec["android_abi"],
                          "ANDROID_PLATFORM": f"android-{spec['android_api']}", "ANDROID_STL": "c++_shared"})
        if spec["os"] == "darwin":
            cache.update({"CMAKE_OSX_DEPLOYMENT_TARGET": "13.0",
                          "CMAKE_OSX_ARCHITECTURES": "x86_64" if spec["arch"] == "amd64" else "arm64"})
        cache.update(overrides or {})
        (build / "CMakeCache.txt").write_text("".join(f"{key}:STRING={value}\n" for key, value in cache.items() if value is not None))
        name = "subconverter_static_full.lib" if spec["os"] == "windows" else "libsubconverter_static_full.a"
        (build / name).write_bytes(f"library fixture for {target}".encode())
        return SDK.package(target, build, self.output, self.version, self.repository)

    def package_all(self):
        for target in SDK.CONFIG["targets"]:
            self.package(target)

    def toolchain_reply(self, build, compiler):
        reply = build / ".cmake/api/v1/reply"
        reply.mkdir(parents=True, exist_ok=True)
        (reply / "toolchains-fixture.json").write_text(json.dumps({
            "toolchains": [{"language": "CXX", "compiler": {"path": compiler}}],
        }))
        (reply / "index-2026-11-04T00-00-00.json").write_text(json.dumps({
            "reply": {"client-subconverter": {"toolchains-v1": {"jsonFile": "toolchains-fixture.json"}}},
        }))

    def test_packages_all_platforms_and_generates_complete_index(self):
        self.package_all()
        SDK.index(self.output, self.version, self.repository)
        document = json.loads((self.output / "subconverter-index.json").read_text())
        self.assertEqual(set(document["artifacts"]), set(SDK.CONFIG["targets"]))
        self.assertEqual(len((self.output / "SHA256SUMS").read_text().splitlines()), 7)
        for target, entry in document["artifacts"].items():
            archive = self.output / f"subconverter-{target}.tar.gz"
            self.assertEqual(SDK.digest(archive), entry["sha256"])
            with tarfile.open(archive) as tar:
                self.assertEqual(set(tar.getnames()), {"lib/libsubconverter.a", "include/node_export.h", "LICENSE", "manifest.json"})
                self.assertTrue(all(member.isfile() for member in tar.getmembers()))
                manifest_bytes = tar.extractfile("manifest.json").read()
                self.assertEqual(SDK.hashlib.sha256(manifest_bytes).hexdigest(), entry["manifest_sha256"])
                self.assertEqual(json.loads(manifest_bytes), entry["manifest"])

    def test_rejects_non_pic_and_wrong_android_platform(self):
        for target, overrides in [
            ("macos-amd64", {"BUILD_WITH_PIC": "OFF"}),
            ("macos-amd64", {"CMAKE_OSX_DEPLOYMENT_TARGET": "15.0"}),
            ("android-arm64", {"ANDROID_ABI": "x86_64"}),
            ("android-arm64", {"ANDROID_PLATFORM": "android-26"}),
            ("android-arm64", {"ANDROID_STL": "c++_static"}),
        ]:
            with self.subTest(target=target, overrides=overrides), self.assertRaises(ValueError):
                self.package(target, overrides)

    def test_rejects_incomplete_release(self):
        self.package("macos-amd64")
        with self.assertRaises(FileNotFoundError):
            SDK.index(self.output, self.version, self.repository)
        self.assertFalse((self.output / "subconverter-index.json").exists())

    def test_resolves_ndk_from_official_toolchain_path(self):
        archive = self.package("android-arm64", {
            "CMAKE_ANDROID_NDK": "",
            "CMAKE_TOOLCHAIN_FILE": str(self.directory / "ndk/build/cmake/android.toolchain.cmake"),
        })
        self.assertTrue(archive.is_file())

    def test_packages_android_without_cached_compiler(self):
        for target in ["android-arm", "android-arm64", "android-amd64"]:
            with self.subTest(target=target):
                compiler = f"/fixture/{target}/ndk/bin/clang++"
                self.toolchain_reply(self.directory / target, compiler)
                archive = self.package(target, {"CMAKE_CXX_COMPILER": None})
                self.assertTrue(archive.is_file())
                self.command_mock.assert_any_call(compiler, "--version")

    def test_prefers_effective_ndk_compiler_over_cached_host_compiler(self):
        compiler = "/fixture/android/ndk/bin/clang++"
        self.toolchain_reply(self.directory / "android-arm64", compiler)
        self.package("android-arm64", {"CMAKE_CXX_COMPILER": "host-g++"})
        self.command_mock.assert_any_call(compiler, "--version")
        self.assertNotIn(unittest.mock.call("host-g++", "--version"), self.command_mock.call_args_list)

    def test_missing_compiler_metadata_requests_reconfiguration(self):
        with self.assertRaisesRegex(ValueError, "Reconfigure with scripts/build-native.py"):
            self.package("android-arm64", {"CMAKE_CXX_COMPILER": None})

    @unittest.skipUnless(shutil.which("cmake") and shutil.which("c++"), "requires CMake 3.20+ and a CXX compiler")
    def test_real_cmake_toolchain_reports_non_cached_compiler(self):
        source = self.directory / "probe"
        source.mkdir()
        compiler = Path(shutil.which("c++")).as_posix()
        (source / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.14)\nproject(compiler_probe LANGUAGES CXX)\n"
        )
        (source / "toolchain.cmake").write_text(f'set(CMAKE_CXX_COMPILER "{compiler}")\n')
        build = source / "build"
        BUILD.request_toolchain_metadata(build)
        result = subprocess.run([
            "cmake", "-S", str(source), "-B", str(build),
            f"-DCMAKE_TOOLCHAIN_FILE={source / 'toolchain.cmake'}",
        ], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        cache = SDK.cache_values(build)
        self.assertNotIn("CMAKE_CXX_COMPILER", cache)
        self.assertEqual(SDK.compiler_path(build, cache), compiler)

    def test_rejects_corrupt_archive(self):
        self.package_all()
        (self.output / "subconverter-macos-amd64.tar.gz").write_bytes(b"modified archive")
        with self.assertRaises(ValueError):
            SDK.index(self.output, self.version, self.repository)

    def test_rejects_mixed_source_commits(self):
        self.package_all()
        path = self.output / "macos-amd64.json"
        entry = json.loads(path.read_text())
        entry["manifest"]["source_commit"] = "b" * 40
        path.write_text(json.dumps(entry))
        with self.assertRaisesRegex(ValueError, "same source commit"):
            SDK.index(self.output, self.version, self.repository)


if __name__ == "__main__":
    unittest.main()
