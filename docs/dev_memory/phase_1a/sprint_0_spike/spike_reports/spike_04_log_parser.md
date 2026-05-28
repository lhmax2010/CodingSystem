# Spike 04: LogErrorParser Coverage

## 假设

`LogErrorParser` 可以在真实 Tizen build failure log 上解析 Phase 1A 关注的 5 类 `error_type`：

- `undefined_reference`
- `undefined_symbol`
- `cannot_find_header`
- `type_mismatch`
- `template_error`

S0-04 只验证真实日志样本覆盖度与 parser 可行性；不实现产品代码，不提交 raw build log。

## 执行环境

| 项 | 值 |
|---|---|
| Repo | `platform/core/appfw/pkgmgr-info` |
| Branch | `tizen_10.0` |
| Primary sample commit | `c2bf5240083784312290b56bbf5a27ff6b7de1c0` (`Fix build for Clang compiler`) |
| Parent tested | `cfaff34ff0cf9a732650eb61bfc9280cffff14d9` |
| Fixed commit tested | `c2bf5240083784312290b56bbf5a27ff6b7de1c0` |
| Flag-trigger experiment source | `469d442d9e1323d389d33f4689933c692c097429` |
| GBS config | `/home/linhao/Toolchain/gbs_llvm.conf` |
| GBS | `2.0.6` |
| Compiler observed | `x86_64-tizen-linux-gnu-clang`, Clang `21.1.1` |

Commands used:

```bash
gbs -c /home/linhao/Toolchain/gbs_llvm.conf build -A x86_64 \
  --include-all --skip-srcrpm --threads 1 --overwrite --keep-packs \
  --buildroot /tmp/coding-system-s0/gbs-root-pkgmgr-llvm \
  /tmp/coding-system-s0/repos/pkgmgr-info-c2bf524-parent-clone
```

```bash
gbs -c /home/linhao/Toolchain/gbs_llvm.conf build -A x86_64 \
  --include-all --skip-srcrpm --threads 1 --overwrite --keep-packs \
  --buildroot /tmp/coding-system-s0/gbs-root-pkgmgr-llvm \
  /tmp/coding-system-s0/repos/pkgmgr-info-c2bf524-fixed-clone
```

Raw logs remain under `/tmp/coding-system-s0/` and are not committed.

## Observed Real Sample

Both `c2bf524^` and `c2bf524` fail under the current LLVM toolchain reference before reaching the linker stage. The repeated hard error is `cannot_find_header`.

Bounded excerpt, with build-root paths normalized:

```text
[SOURCE_ROOT]/src/parser/include/pkgmgr_parser.h:44:10: fatal error: 'libxml/xmlreader.h' file not found
   44 | #include <libxml/xmlreader.h>
      |          ^~~~~~~~~~~~~~~~~~~~
```

Structured count from the two real GBS runs:

| Run | Repeated hard diagnostics | Classified type |
|---|---:|---|
| `c2bf524^` | 8 | `cannot_find_header` |
| `c2bf524` | 8 | `cannot_find_header` |

No observed hard diagnostics matched `undefined_reference`, `undefined_symbol`, `type_mismatch`, or `template_error` in these logs.

## Commit Cross-check

`c2bf524` is a real toolchain migration build-fix commit and its commit message references several useful categories, including linker undefined functions and Clang C++ diagnostics.

However, under the current `/home/linhao/Toolchain/gbs_llvm.conf` repos, both the parent and `c2bf524` are blocked earlier by the `libxml/xmlreader.h` include failure. A later real commit, `510e1a555166bd838f6482e7b6dc730650247795` (`Remove libxml2 include statement from pkgmgr_parser.h`), removes that include from `src/parser/include/pkgmgr_parser.h`. That explains why the current observed failure is a `cannot_find_header` sample rather than the linker/type/template failures described by `c2bf524`.

## Flag-trigger Experiments

Per user direction, I then kept `pkgmgr-info` business source unchanged and only changed compile/link flags to trigger real migration failures. Raw logs remain under `/tmp/coding-system-s0/` and are not committed.

### Experiment A: LLD strict undefined symbols

Flags:

```bash
LDFLAGS="-fuse-ld=lld -Wl,--as-needed -Wl,--no-undefined"
```

Raw logs:

- `/tmp/coding-system-s0/s0_04_A_configure.log`
- `/tmp/coding-system-s0/s0_04_A_build.log`

Result: configure completed; build failed during shared-library link with LLD unresolved symbols.

Observed diagnostics:

| Observed type | Count | Sample feature |
|---|---|---|
| Link unresolved symbol (`undefined_symbol` wording; `undefined_reference` class candidate) | 20 | `ld.lld: error: undefined symbol: <symbol>` followed by `>>> referenced by <source>` and object file |

Bounded excerpt:

```text
ld.lld: error: undefined symbol: pkgmgrinfo_updateinfo_get_usr_updateinfo
>>> referenced by pkgmgr_parser_db.c
>>>               CMakeFiles/pkgmgr_parser.dir/src/pkgmgr_parser_db.c.o:(pkgmgr_parser_register_pkg_update_info_in_usr_db)
```

Representative symbols:

- `pkgmgrinfo_basic_free_package`
- `_parser_create_and_initialize_db`
- `tzplatform_getuid`
- `pkgmgrinfo_updateinfo_get_usr_updateinfo`
- `pkgmgrinfo_pkginfo_get_usr_pkginfo`
- `_parser_execute_write_queries`

### Experiment B: libc++ switch

Flags:

```bash
CXXFLAGS="-stdlib=libc++"
LDFLAGS="-stdlib=libc++ -fuse-ld=lld"
```

Raw log:

- `/tmp/coding-system-s0/s0_04_B_configure.log`

Result: CMake did not reach project build. The C++ compiler sanity check failed because the current LLVM GBS buildroot has no `libc++` package/library available.

Observed diagnostic:

| Observed type | Count | Sample feature |
|---|---:|---|
| Missing C++ standard library (`cannot_find_library`, outside the current 5 S0-04 target classes) | 1 | `ld.lld: error: unable to find library -lc++` |

Bounded excerpt:

```text
ld.lld: error: unable to find library -lc++
x86_64-tizen-linux-gnu-clang++: error: linker command failed with exit code 1
```

I checked the current GBS repo metadata and buildroot package set; no Tizen `libc++` / `libcxx` package was visible in this buildroot or its cached repo metadata.

## Triggered Type Summary

This is a factual trigger summary only; S0-04 PASS/FAIL decision is deferred to user review.

| Source | Naturally triggered target class |
|---|---|
| Historical `c2bf524`/`c2bf524^` GBS runs | `cannot_find_header` |
| Experiment A strict LLD link | link unresolved symbol: LLD wording is `undefined_symbol`; parser taxonomy may map it to `undefined_reference` depending on S0-04 policy |
| Experiment B libc++ switch | no target class; triggered missing `-lc++` before project build |

Target classes still not naturally triggered on `pkgmgr-info` with the current inputs:

- `type_mismatch`
- `template_error`

## Conclusion

S0-04 decision is pending.

Current real evidence from `pkgmgr-info` covers `cannot_find_header` and an LLD unresolved-symbol pattern. The libc++ experiment exposed a missing toolchain/runtime package (`-lc++`) before reaching template or type mismatch diagnostics. No synthetic logs were created.
