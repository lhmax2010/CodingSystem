# Spike 01: Tizen Repo Selection

## 假设

Phase 1A Sprint 0 可以选定一个真实 Tizen cmake/ninja project 作为后续 S0-02 ~ S0-09 的验证基线。该 repo 应满足：

- cmake + ninja 路线可用
- 规模小于 100 万行
- 可在 x86 工作站 clone + build
- 有历史 build failure / build fix commit，可为 S0-04 / S0-08 提供真实错误样本
- ground truth 可核对（spike 硬标准）：至少 1-2 个能读 C/C++/CMake 的人可做人工核对；dogfooding 熟悉度为软偏好、非阻塞

## 执行

候选 repo：

| Repo | URL | 结论 |
|---|---|---|
| `platform/core/appfw/pkgmgr-info` | `git://git.tizen.org/platform/core/appfw/pkgmgr-info` | 选定 |
| `platform/core/security/security-manager` | `git://git.tizen.org/platform/core/security/security-manager` | 未选：当前公开 Tizen 10.0 repo 依赖解析失败 |
| `platform/core/multimedia/avsystem` | `git://git.tizen.org/platform/core/multimedia/avsystem` | 未选：当前分支未发现 CMakeLists.txt |

主要命令：

```bash
git clone --depth 1 --branch tizen_10.0 \
  git://git.tizen.org/platform/core/appfw/pkgmgr-info \
  /tmp/coding-system-s0/repos/pkgmgr-info

gbs build -A x86_64 --include-all --skip-srcrpm --threads 1 \
  --buildroot /tmp/coding-system-s0/gbs-root-pkgmgr \
  /tmp/coding-system-s0/repos/pkgmgr-info

gbs build -A x86_64 --include-all --skip-srcrpm --threads 1 \
  --overwrite --extra-packs ninja \
  --buildroot /tmp/coding-system-s0/gbs-root-pkgmgr \
  /tmp/coding-system-s0/repos/pkgmgr-info

cmake -S /home/abuild/s0/pkgmgr-info \
  -B /home/abuild/s0/build-ninja \
  -G Ninja \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DFULLVER=0.35.28 \
  -DMAJORVER=0 \
  -DUNITDIR=/usr/lib/systemd/system \
  -DASAN_ENABLED=FALSE

ninja -C /home/abuild/s0/build-ninja -j2 pkgmgr-info
```

说明：`cmake` / `ninja` 验证在隔离 GBS buildroot 内执行；本机 host 没有安装 `cmake` / `ninja`，但 GBS buildroot 中可从 Tizen Base repo 安装并使用。

## 数据

### 选定 repo

| 项 | 值 |
|---|---|
| Repo | `platform/core/appfw/pkgmgr-info` |
| Remote | `git://git.tizen.org/platform/core/appfw/pkgmgr-info` |
| Branch | `tizen_10.0` |
| HEAD | `469d442d9e1323d389d33f4689933c692c097429` |
| Git history | 1617 commits after unshallow |
| Public contributors | 67 unique authors in full history |
| CMake entry points | 8 `CMakeLists.txt` files |
| RPM spec | `packaging/pkgmgr-info.spec` |
| Estimated C/C++/CMake LOC | 48,588 lines across 310 files |

LOC command:

```bash
find /tmp/coding-system-s0/repos/pkgmgr-info -type f \
  \( -name '*.c' -o -name '*.cc' -o -name '*.cpp' -o -name '*.cxx' \
     -o -name '*.h' -o -name '*.hh' -o -name '*.hpp' \
     -o -name 'CMakeLists.txt' \) -print0 | xargs -0 wc -l | tail -n 1
```

Observed output:

```text
48588 total
```

### Build verification

GBS build:

| Check | Result |
|---|---|
| x86_64 GBS build | succeeded |
| CTest | 33/33 tests passed |
| RPMs produced | yes |
| Buildroot | `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0` |
| Report | `/tmp/coding-system-s0/gbs-root-pkgmgr/local/repos/tizen/x86_64/index.html` |
| Log path | `/tmp/coding-system-s0/gbs-root-pkgmgr/local/repos/tizen/x86_64/logs/success/pkgmgr-info-0.35.28-1/log.txt` |

Bounded evidence excerpts:

```text
100% tests passed, 0 tests failed out of 1
[  PASSED  ] 33 tests.
Wrote: /home/abuild/rpmbuild/RPMS/x86_64/pkgmgr-info-0.35.28-1.x86_64.rpm
```

Raw build logs are intentionally not committed to the repo, per Raw Log constraints.

### Ninja route verification

After installing `ninja` into the same GBS buildroot with `--extra-packs ninja`:

```text
/usr/bin/ninja
1.12.1
/usr/bin/cmake
cmake version 3.31.2
```

CMake Ninja configure generated:

| Artifact | Value |
|---|---|
| `compile_commands.json` | generated |
| Lines | 1219 |
| Size | 408,333 bytes |
| Path | `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/build-ninja/compile_commands.json` |

Ninja target build:

```text
[98/99] Linking CXX shared library src/libpkgmgr-info.so.0.35.28
[99/99] Creating library symlink src/libpkgmgr-info.so.0 src/libpkgmgr-info.so
NINJA_TARGET_OK
```

### Historical build failure / fix evidence

Full history contains multiple build-fix commits. Best S0-04/S0-08 seed:

| Commit | Date | Subject | Why useful |
|---|---|---|---|
| `c2bf5240083784312290b56bbf5a27ff6b7de1c0` | 2025-12-09 | `Fix build for Clang compiler` | Directly relevant to GCC -> Clang / LLVM-stack migration errors |

Commit summary:

```text
Fix build for Clang compiler

Fix linker error "undefined functions".
Fix warning "unused variable".
Fix warning "destructor called on non-final class that has virtual functions but non-virtual destructor".
Fix error "variable-sized object may not be initialized".
Fix warning "variable length arrays in C++ are a Clang extension".
Fix error "explicitly defaulted move assignment operator is implicitly deleted".
```

Other build-fix candidates observed:

```text
8eeea4c 2023-12-27 Fix build error
9140b28 2023-01-16 Fix build error
d77dc1f 2021-12-14 Fix build error for new glib
d8ec167 2021-03-23 Fix 64-bit build error
```

### Rejected candidate notes

`security-manager`:

- Meets CMake and size expectations.
- Current public Tizen 10.0 GBS dependency resolution failed:

```text
nothing provides pkgconfig(cynara-uid-creds) >= 0.24.0
```

`avsystem`:

- Current tested branch did not contain `CMakeLists.txt`; rejected for S0-01.

## 结论

Selected repo: `platform/core/appfw/pkgmgr-info`.

Machine-verifiable S0-01 criteria are satisfied:

| Acceptance | Result | Evidence |
|---|---|---|
| cmake + ninja | satisfied | CMake configured with `-G Ninja`; `ninja -C ... pkgmgr-info` succeeded |
| < 100 万行 | satisfied | 48,588 C/C++/CMake LOC |
| clone + build on x86 workstation | satisfied | GBS x86_64 build succeeded; CTest 33/33 passed; RPMs produced |
| historical build failure commit | satisfied | `c2bf524` and other build-fix commits found |
| ground truth 可核对 | satisfied | user confirmed `pkgmgr-info` satisfies the spike hard standard; repo is 48,588 LOC and does not require a senior repo owner |

S0-01 is complete. `pkgmgr-info` is confirmed as the Phase 1A validation baseline.

## 影响

- S0-02 can use the already validated CMake/Ninja route to focus on compile_commands coverage and include/define completeness.
- S0-03 can use the generated compile database as the starting point for clangd startup/indexing validation.
- S0-04/S0-08 can seed realistic compile-failure cases from `c2bf524^` vs `c2bf524`, especially Clang-specific diagnostics.
- `security-manager` remains a useful secondary demo candidate, but not the Sprint 0 primary repo because its current public repo dependency set did not resolve in this workstation run.

## 后续动作

1. Proceed to S0-02: compile_commands.json generation validation on the selected repo.
2. Use `c2bf524` (`Fix build for Clang compiler`) as the preferred real toolchain-migration build-fix sample for S0-04 and S0-08.
3. Do not start S0-10 unless explicitly requested.

## Artifact 路径

- Local clone: `/tmp/coding-system-s0/repos/pkgmgr-info`
- GBS buildroot: `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0`
- GBS report: `/tmp/coding-system-s0/gbs-root-pkgmgr/local/repos/tizen/x86_64/index.html`
- Bounded Ninja build log: `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/ninja_build_pkgmgr_info.log`
- `compile_commands.json`: `/tmp/coding-system-s0/gbs-root-pkgmgr/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/s0/build-ninja/compile_commands.json`
