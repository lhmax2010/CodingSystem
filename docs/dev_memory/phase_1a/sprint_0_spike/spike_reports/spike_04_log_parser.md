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

## Coverage Status

S0-04 is blocked by sample coverage. I did not fabricate logs or synthetic diagnostics.

| Acceptance | Status | Evidence |
|---|---|---|
| Collect 50 Tizen historical build failure logs | BLOCKED | 2 real GBS runs available, both same package/version and same failure class |
| `undefined_reference` >= 80% | NOT EVALUABLE | 0 real samples observed |
| `undefined_symbol` >= 80% | NOT EVALUABLE | 0 real samples observed |
| `cannot_find_header` >= 80% | PARTIAL | Real sample observed; parser coverage can be validated only for this one class so far |
| `type_mismatch` >= 70% | NOT EVALUABLE | 0 real samples observed |
| `template_error` >= 70% | NOT EVALUABLE | 0 real samples observed |
| false positive <= 10% | NOT EVALUABLE | Need mixed real corpus, including out-of-scope diagnostics |

## Required Inputs To Continue

To complete S0-04 without fake data, we need additional real LLVM toolchain migration failure inputs:

- Preferred: 50 historical Tizen build failure logs from LLVM GBS/CI, with enough examples across the 5 target classes.
- Also OK: package repositories plus failing commits/refs that reproduce under `/home/linhao/Toolchain/gbs_llvm.conf`.
- Minimum useful next batch: at least one real package/log set for each missing class: `undefined_reference`, `undefined_symbol`, `type_mismatch`, and `template_error`.

For package-code based reproduction, please provide package repo path/name, branch or commit, and whether the failure is expected on `x86_64` with the current LLVM GBS config.

## Conclusion

S0-04 is not passed yet.

Status: BLOCKED by insufficient real log coverage. The available `pkgmgr-info` sample validates a real `cannot_find_header` shape, but it cannot support the required 5-class coverage table or 50-log accuracy calculation.
