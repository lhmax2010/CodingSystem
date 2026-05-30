# Spike 02: compile_commands.json Generation

## 假设

`pkgmgr-info` 在隔离 GBS buildroot 内可以通过 CMake + Ninja 生成完整、可被 clangd/CNEI 后续 spike 使用的 `compile_commands.json`。

S0-02 只验证编译数据库生成与覆盖质量；不启动 S0-10 scale spike，不实现产品代码。

## 执行

基线 repo：

| 项 | 值 |
|---|---|
| Repo | `platform/core/appfw/pkgmgr-info` |
| Branch | `tizen_10.0` |
| HEAD | `469d442d9e1323d389d33f4689933c692c097429` |
| Source in chroot | `/home/abuild/s0/pkgmgr-info` |
| Build dir in chroot | `/home/abuild/s0/build-s0-02` |
| Host buildroot | `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0` |

主要命令：

```bash
printf 'set -e
rm -rf /home/abuild/s0/build-s0-02
cmake -S /home/abuild/s0/pkgmgr-info \
  -B /home/abuild/s0/build-s0-02 \
  -G Ninja \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_VERBOSE_MAKEFILE=ON \
  -DCMAKE_INSTALL_PREFIX:PATH=/usr \
  -DCMAKE_INSTALL_LIBDIR:PATH=/usr/lib64 \
  -DINCLUDE_INSTALL_DIR:PATH=/usr/include \
  -DLIB_INSTALL_DIR:PATH=/usr/lib64 \
  -DSYSCONF_INSTALL_DIR:PATH=/etc \
  -DSHARE_INSTALL_PREFIX:PATH=/usr/share \
  -DLIB_SUFFIX=64 \
  -DCMAKE_SKIP_RPATH:BOOL=ON \
  -DBUILD_SHARED_LIBS:BOOL=ON \
  -DFULLVER=0.35.28 \
  -DMAJORVER=0 \
  -DUNITDIR=/usr/lib/systemd/system \
  -DASAN_ENABLED=FALSE \
  >/home/abuild/s0/s0_02_cmake_configure.log 2>&1
test -s /home/abuild/s0/build-s0-02/compile_commands.json
ninja -C /home/abuild/s0/build-s0-02 -j2 \
  >/home/abuild/s0/s0_02_ninja_build.log 2>&1
echo S0_02_GENERATE_AND_BUILD_OK
exit
' | gbs chroot /tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0
```

Observed result:

```text
S0_02_GENERATE_AND_BUILD_OK
```

## 数据

Generated artifact:

| 项 | 值 |
|---|---|
| Path | `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/build-s0-02/compile_commands.json` |
| JSON parse | valid |
| Lines | 1219 |
| Size | 408,333 bytes |
| Entries | 203 |
| Unique compile files | 153 |
| Repo C/C++ translation units | 153 |
| Missing source files | 0 |
| Extra compile files | 0 |
| Entries with `output` | 203 |

Coverage note: 203 compile command entries map to 153 unique C/C++ translation units because some sources are compiled by more than one target/configuration. The S0-02 coverage check is based on unique source files.

Compiler / wrapper shape:

| Check | Result |
|---|---|
| `/usr/bin/cc` entries | 5 |
| `/usr/bin/c++` entries | 198 |
| `-std=c++17` observed | yes |
| `--sysroot` entries | 0 |
| wrapper-like command entries | 0 |

The selected S0-01 baseline is a native x86_64 GBS chroot build, so the cross-compile/sysroot wrapper clause is not applicable for this repo/configuration. No wrapper or sysroot path is being hidden from `compile_commands.json`.

Include/define completeness checks:

| Check | Result |
|---|---|
| Unique include paths | 34 |
| Unique defines | 9 |
| Missing expected local includes | 0 |
| Missing expected system/pkg-config includes | 0 |
| Required `LIB_PATH` define | present: `-DLIB_PATH="/usr/lib64"` |
| Required `SYSCONFDIR` define | present: `-DSYSCONFDIR="/etc"` |

Observed define set:

```text
-DGTEST_HAS_PTHREAD=1
-DLIB_PATH="/usr/lib64"
-DSYSCONFDIR="/etc"
-DTIZEN_MAJOR_VER="0"
-DTIZEN_MINOR_VER="0"
-DTIZEN_PATCH_VER=""
-Dpkgmgr_info_EXPORTS
-Dpkgmgr_info_server_EXPORTS
-Dpkgmgr_parser_EXPORTS
```

Expected include categories observed:

- Local project include roots: `include`, `src`, `src/parser/include`, `src/common`, `src/server`, `tool/SYSTEM`
- Tizen/system include roots: `dlog`, `glib-2.0`, `system`, `libxml2`, `parcel`, `vconf`, `cynara`, `gio-unix-2.0`, `minizip`, `tizen-database`, `tizen-libopener`

Bounded Ninja build evidence:

```text
[210/214] Linking C executable tool/pkg-db-recovery
[211/214] Linking C executable tool/pkg-db-creator
[212/214] Building CXX object test/unit_tests/CMakeFiles/pkgmgr-info-unit-test.dir/mock/system_info_mock.cc.o
[213/214] Linking CXX executable src/server/pkginfo-server
[214/214] Linking CXX executable test/unit_tests/pkgmgr-info-unit-test
```

Sample compile database excerpt:

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_02_compile_commands_sample.json`

The sample contains three real entries with `${SOURCE_ROOT}` and `${BUILD_DIR}` placeholders: one C tool source, one client C++ source, and one server C++ source.

Raw configure/build logs are not committed. This report only records bounded excerpts and structured counts.

## 结论

S0-02 PASS.

Acceptance status:

| Acceptance | Result | Evidence |
|---|---|---|
| `compile_commands.json` can be generated | satisfied | CMake configured with `-G Ninja -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`; non-empty JSON produced |
| 100% source file coverage | satisfied | 153/153 unique C/C++ translation units covered |
| include paths / defines complete | satisfied | expected local and system include categories present; required defines present |
| cross/sysroot wrapper handled if applicable | not applicable | native x86_64 GBS chroot uses direct `/usr/bin/cc` and `/usr/bin/c++`; no hidden wrapper/sysroot observed |
| generated database compiles | satisfied | `ninja -C /home/abuild/s0/build-s0-02 -j2` reached 214/214 |

## 影响

- S0-03 can use `/home/abuild/s0/build-s0-02/compile_commands.json` as the clangd startup/indexing baseline.
- S0-04 and S0-08 should prioritize `c2bf5240083784312290b56bbf5a27ff6b7de1c0` (`Fix build for Clang compiler`) as the real toolchain-migration sample, per user confirmation.
- S0-10 remains out of scope until explicitly started.

## Artifact 路径

- Host `compile_commands.json`: `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/build-s0-02/compile_commands.json`
- Configure log (not committed): `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/s0_02_cmake_configure.log`
- Ninja log (not committed): `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/s0_02_ninja_build.log`
