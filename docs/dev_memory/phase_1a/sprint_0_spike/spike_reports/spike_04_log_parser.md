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

## Parser Rule Lock

Before the expanded experiments, I fixed a spike-only generic parser and did not tune it after seeing the new logs.

| Item | Value |
|---|---|
| Parser artifact | `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_04_log_parser.py` |
| Rule version | `spike_04_generic_v1` |
| SHA256 at experiment start | `9a86dc8ad0de7a4f0819ee1ae36acb736374d86104fc76585f939aae2363e544` |
| Pattern families | `cannot_find_header`, `undefined_reference`, `undefined_symbol`, `type_mismatch`, `template_error` |
| Primary policy | `first_parsed_error_only_no_cascade_analysis` |

Rule gap known before judging S0-04: this parser does not classify `unknown type name` and does not separate primary/cascade errors.

## Experiment 1: Basic Type Coverage

All source edits were made in disposable copies under `/tmp/coding-system-s0/experiments/`. The baseline repo `/tmp/coding-system-s0/repos/pkgmgr-info` stayed clean. Raw logs and diffs are under `/tmp/coding-system-s0/` and are not committed.

Common build note: the standalone CMake runs use Clang 21.1.1 from the LLVM GBS buildroot. I set `CFLAGS/CXXFLAGS=-Wno-error=unused-command-line-argument` to avoid unrelated Clang 21 `-Wl,... input unused` noise from stopping compilation before the intended error.

| Case | Temporary change | Diff | Raw log | Parser result | Format feature |
|---|---|---|---|---|---|
| 1.1 `cannot_find_header` | Removed `${CMAKE_SOURCE_DIR}/src/parser/include` from root `INCLUDE_DIRECTORIES` | `/tmp/coding-system-s0/exp1_1_header.diff` | `/tmp/coding-system-s0/s0_04_exp1_1_build.log` | `cannot_find_header: 1` | `fatal error: 'pkgmgr_parser.h' file not found` |
| 1.2 `undefined_reference` | Removed `${TARGET_LIB_PKGMGR_SERVER}` from `pkginfo-server` link line. An earlier removal of parser from `pkg-db-recovery` did not fail and is preserved in the diff. | `/tmp/coding-system-s0/exp1_2_link.diff` | `/tmp/coding-system-s0/s0_04_exp1_2_build.log` | `undefined_reference: 5` | `undefined reference to \`pkgmgr_server::...\`` |
| 1.3 `type_mismatch` | Changed `AbstractParcelable::WriteInt(..., int)` declaration to `const char*` only in header | `/tmp/coding-system-s0/exp1_3_type.diff` | `/tmp/coding-system-s0/s0_04_exp1_3_build.log` | `type_mismatch: 3` | `cannot initialize a parameter of type 'const char *' with an lvalue of type ...` |
| 1.4 `template_error` | Changed `std::vector<int>` to invalid `std::vector<int, std::string>` allocator form | `/tmp/coding-system-s0/exp1_4_template.diff` | `/tmp/coding-system-s0/s0_04_exp1_4_build.log` | `template_error: 1` | `static assertion failed ... std::vector must have the same value_type as its allocator` |
| 1.5 upgrade header rename | Not run as a new synthetic edit | Existing historical sample | `/tmp/coding-system-s0/pkgmgr-info-c2bf524-parent-fail-log.txt` | `cannot_find_header` shape observed earlier | `libxml/xmlreader.h` include failure, later fixed by `510e1a5` removing the include |

Bounded samples:

```text
/home/abuild/s0/s0_04_exp1_1_src/src/common/pkgmgrinfo_appinfo.cc:35:10: fatal error: 'pkgmgr_parser.h' file not found
```

```text
main.cc:(.text+0x198): undefined reference to `pkgmgr_server::Daemonizer::Daemonizer()'
/usr/bin/ld: main.cc:(.text+0x1a1): undefined reference to `pkgmgr_server::Daemonizer::Daemonize()'
```

```text
/home/abuild/s0/s0_04_exp1_3_src/src/common/parcel/abstract_parcelable.cc:132:20: error: cannot initialize a parameter of type 'const char *' with an lvalue of type 'const ParcelableType'
```

```text
bits/stl_vector.h:443:21: error: static assertion failed due to requirement 'is_same<char, int>::value': std::vector must have the same value_type as its allocator
note: in instantiation of template class 'std::vector<int, std::basic_string<char>>' requested here
```

Previous flag-only experiment still covers LLD wording:

| Case | Flags | Raw log | Parser result | Feature |
|---|---|---|---|---|
| LLD strict undefined symbols | `LDFLAGS="-fuse-ld=lld -Wl,--as-needed -Wl,--no-undefined"` | `/tmp/coding-system-s0/s0_04_A_build.log` | `undefined_symbol: 20` | `ld.lld: error: undefined symbol: <symbol>` |

The `libc++` switch experiment still stops before project build because the buildroot cannot find `-lc++`; it is recorded as a toolchain dependency gap, not a target S0-04 parser class.

## Experiment 2: Cascade Error Test

Chosen trigger: way B, rename a widely used typedef in a public header.

Temporary change:

```diff
-typedef void *pkgmgrinfo_pkginfo_h;
+typedef void *pkgmgrinfo_pkginfo_h_renamed_for_s0_04;
```

Raw artifacts:

- Diff: `/tmp/coding-system-s0/exp2_cascade.diff`
- Configure log: `/tmp/coding-system-s0/s0_04_exp2_configure.log`
- Build log: `/tmp/coding-system-s0/s0_04_exp2_build.log`
- Parser output: `/tmp/coding-system-s0/s0_04_exp2_parsed.json`

Observed cascade:

| Item | Value |
|---|---:|
| Total `error:` lines | 41 |
| `unknown type name 'pkgmgrinfo_pkginfo_h'` lines | 39 |
| Compiler `too many errors emitted` lines | 2 |
| Parser parsed independent errors | 0 |
| Parser identified primary | No |
| Primary position in compiler error list | 1 |

Ground truth primary: `include/pkgmgrinfo_type.h` typedef was renamed at line 188, removing the public API type `pkgmgrinfo_pkginfo_h`. The first compiler error is already a direct symptom of that primary:

```text
/home/abuild/s0/s0_04_exp2_src/include/pkgmgrinfo_type.h:278:46: error: unknown type name 'pkgmgrinfo_pkginfo_h'; did you mean 'pkgmgrinfo_appinfo_h'?
```

Primary/cascade gap: `spike_04_generic_v1` does not classify `unknown_type_name`, so it returns 0 errors for this cascade log and cannot distinguish primary from cascade. This is relevant to Sprint 1+ design: LogErrorParser either needs `unknown_type_name` support and primary heuristics, or CNEI needs a separate causality layer before relying on one-error-per-packet behavior.

## Experiment 3: Determinism And Token Evaluation

The same Experiment 2 cascade log was parsed three times.

| Run | SHA256 |
|---|---|
| run 1 | `8d115d3a3e385d823e81bd9d79c63b058d042757e144be3a0ee2a7bdec9f93ff` |
| run 2 | `8d115d3a3e385d823e81bd9d79c63b058d042757e144be3a0ee2a7bdec9f93ff` |
| run 3 | `8d115d3a3e385d823e81bd9d79c63b058d042757e144be3a0ee2a7bdec9f93ff` |

Result: deterministic for this log.

Token estimator: `tiktoken` was not installed in this environment, so I used the documented fallback estimate `ceil(chars / 4)` over the exact strings. Raw build log is used only for token comparison baseline; it is not sent to an LLM prompt and is not committed.

Token comparison for `/tmp/coding-system-s0/s0_04_exp2_build.log`:

| Mode | Packet count | Estimated tokens | Ratio vs primary |
|---|---:|---:|---:|
| A raw build log as prompt baseline | 1 | 8,960 | 26.35x |
| B one packet per compiler `error:` line | 41 | 8,679 | 25.53x |
| C one primary packet with cascade summary | 1 | 340 | 1.00x |

Generated comparison artifacts:

- `/tmp/coding-system-s0/s0_04_exp2_error_packets.json`
- `/tmp/coding-system-s0/s0_04_exp2_primary_packet.json`
- `/tmp/coding-system-s0/s0_04_exp2_token_eval.json`

## Revert / Cleanup Check

No edits were made to `/tmp/coding-system-s0/repos/pkgmgr-info`; `git -C /tmp/coding-system-s0/repos/pkgmgr-info status -sb` stayed clean after experiments. The modified experiment trees are disposable and can be removed with:

```bash
rm -rf /tmp/coding-system-s0/experiments
```

No raw logs or temporary package source copies are committed.

## Conclusion

S0-04 decision is pending user review.

Factual result: single-error mechanism coverage now has real samples for all five target parser formats when including the earlier LLD strict-link experiment: `cannot_find_header`, `undefined_reference`, `undefined_symbol`, `type_mismatch`, and `template_error`. The important unresolved gap is not basic regex coverage; it is cascade handling and primary/root-cause identification. The current spike parser is deterministic, but it does not classify `unknown_type_name` and does not distinguish primary from cascade.
