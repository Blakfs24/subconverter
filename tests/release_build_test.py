"""Configure real release targets against isolated system dependency fixtures."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("cmake") and shutil.which("pkg-config"), "requires CMake and pkg-config")
class ReleaseBuildTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="release-config-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.prefix = self.directory / "system"
        self.include = self.prefix / "include"
        self.lib = self.prefix / "lib"
        self.cron = self.prefix / "cron-include"
        self.date = self.prefix / "date-include"
        headers = {
            self.include / "quickjs/quickjs.h": "",
            self.include / "curl/curlver.h": '#define LIBCURL_VERSION "8.6.0"\n',
            self.include / "curl/curl.h": "",
            self.cron / "libcron/Cron.h": "",
            self.date / "date/date.h": "",
        }
        for path, text in headers.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        for name in ["libyaml-cpp.a", "libpcre2-8.a", "liblibcron.a", "quickjs/libquickjs.a", "libcurl.tbd"]:
            path = self.lib / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"!<arch>\n")
        pkgconfig = self.lib / "pkgconfig"
        pkgconfig.mkdir()
        for name, library in [("yaml-cpp", "yaml-cpp"), ("libpcre2-8", "pcre2-8")]:
            (pkgconfig / f"{name}.pc").write_text(
                f"prefix={self.prefix.as_posix()}\nlibdir=${{prefix}}/lib\nincludedir=${{prefix}}/include\n"
                f"Name: {name}\nDescription: isolated system dependency fixture\nVersion: 1.0.0\n"
                f"Libs: -L${{libdir}} -l{library}\nCflags: -I${{includedir}}\n"
            )
        self.environment = {**os.environ, "PKG_CONFIG_PATH": str(pkgconfig), "PKG_CONFIG_LIBDIR": str(pkgconfig)}

    def configure(self, executable):
        build = self.directory / "build"
        query = build / ".cmake/api/v1/query/codemodel-v2"
        query.parent.mkdir(parents=True)
        query.touch()
        result = subprocess.run([
            "cmake", "-S", str(ROOT), "-B", str(build),
            f"-DCMAKE_PREFIX_PATH={self.prefix}",
            f"-DRAPIDJSON_INCLUDE_DIRS={self.include}", f"-DTOML11_INCLUDE_DIRS={self.include}",
            f"-DLIBCRON_INCLUDE_DIR={self.cron}", f"-DDATE_INCLUDE_DIR={self.date}",
            f"-DCURL_LIBRARY={self.lib / 'libcurl.tbd'}", f"-DCURL_INCLUDE_DIR={self.include}",
            "-DCURL_NO_CURL_CMAKE=TRUE", "-DAUTO_FETCH_DEPS=OFF", "-DFORCE_FETCH_DEPS=OFF",
            f"-DBUILD_RELEASE_APP={'ON' if executable else 'OFF'}",
            f"-DBUILD_STATIC_LIBRARY={'OFF' if executable else 'ON'}", "-DBUILD_FULL_STATIC=OFF",
        ], env=self.environment, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        reply = build / ".cmake/api/v1/reply"
        index = json.loads(sorted(reply.glob("index-*.json"))[-1].read_text())
        codemodel = json.loads((reply / index["reply"]["codemodel-v2"]["jsonFile"]).read_text())
        targets = codemodel["configurations"][0]["targets"]
        self.assertEqual([target["name"] for target in targets], ["subconverter" if executable else "subconverter_static"])
        return json.loads((reply / targets[0]["jsonFile"]).read_text())

    def test_executable_uses_system_libraries_without_static_bundling(self):
        target = self.configure(executable=True)
        self.assertEqual(target["type"], "EXECUTABLE")
        includes = {entry["path"] for group in target["compileGroups"] for entry in group.get("includes", [])}
        self.assertIn(self.include.as_posix(), includes)
        self.assertIn(self.cron.as_posix(), includes)
        self.assertIn(self.date.as_posix(), includes)
        link = " ".join(fragment["fragment"] for fragment in target["link"]["commandFragments"])
        for name in ["libyaml-cpp.a", "libpcre2-8.a", "libcurl.tbd"]:
            self.assertIn((self.lib / name).as_posix(), link)

    def test_unbundled_static_library_accepts_system_dependencies(self):
        target = self.configure(executable=False)
        self.assertEqual(target["type"], "STATIC_LIBRARY")
        includes = {entry["path"] for group in target["compileGroups"] for entry in group.get("includes", [])}
        self.assertIn(self.include.as_posix(), includes)


if __name__ == "__main__":
    unittest.main()
