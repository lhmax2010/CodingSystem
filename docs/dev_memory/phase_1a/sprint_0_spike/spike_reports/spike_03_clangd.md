# Spike 03: clangd Startup, Indexing, and Accuracy

## 假设

`pkgmgr-info` 的真实 Tizen C/C++ 代码在 S0-02 生成的 `compile_commands.json` 下，可以用 clangd 作为 CNEI preferred backend，满足 Phase 1A 对 definition / references 的语义准确率要求。

S0-03 只验证 clangd 启动、索引、准确率和 compile database mtime 可读性；完整 stale 触发、confidence 降级和 Evidence Packet 顶层字段验证留到 S0-09。

## 执行环境

| 项 | 值 |
|---|---|
| Repo | `platform/core/appfw/pkgmgr-info` |
| Branch | `tizen_10.0` |
| HEAD | `469d442d9e1323d389d33f4689933c692c097429` |
| Source in chroot | `/home/abuild/s0/pkgmgr-info` |
| Build dir in chroot | `/home/abuild/s0/build-s0-02` |
| `compile_commands.json` | `/home/abuild/s0/build-s0-02/compile_commands.json` |
| clangd | `clangd version 19.1.4` |
| clangd package source | Tizen Base `clang-19.1.4-5.5.x86_64` |

clangd was installed into the same GBS buildroot with:

```bash
gbs build -A x86_64 --include-all --skip-srcrpm --threads 1 \
  --overwrite --extra-packs ninja,clang --keep-packs \
  --buildroot /tmp/coding-system-s0/gbs-root-pkgmgr \
  /tmp/coding-system-s0/repos/pkgmgr-info
```

The LSP spike driver is stored as dev-memory only:

- `docs/dev_memory/phase_1a/sprint_0_spike/spike_reports_data/spike_03_clangd_lsp_eval.py`

## Sampling Method

The random source follows the SPRINT_0 prompt's `shuf` method:

```bash
cd /tmp/coding-system-s0/repos/pkgmgr-info
rg --type=cpp -o '\b[A-Z][a-zA-Z]+\b' --no-line-number src/ | sort -u | shuf -n 400
rg --type=cpp -o '\b[A-Z][a-zA-Z]+\b' --no-line-number src/ | sort -u | shuf -n 240
```

The prompt command emits `path:symbol` rows because it keeps filenames. S0-03 preserves that behavior and uses the sampled path as the query file.

The raw regex also samples license/comment words such as `Copyright`, `License`, and `BASIS`. Those are not code tokens and cannot be meaningful clangd LSP queries. To avoid hand-picking easy symbols, the spike used the shuffled stream as an ordered random candidate stream and selected the first 50 definition candidates / first 30 reference candidates that had at least one occurrence outside comments and string literals in the sampled file.

| Sample | Candidate stream | Excluded before fill | Exclusion reason | Final sample |
|---|---:|---:|---|---:|
| definition | 400 | 85 | only comment/string occurrences | 50 |
| references | 240 | 55 | only comment/string occurrences | 30 |

Artifacts:

- `spike_03_definition_candidate_stream.txt`
- `spike_03_references_candidate_stream.txt`
- `spike_03_definition_sample_semantic.json`
- `spike_03_references_sample_semantic.json`
- `spike_03_definition_sample_excluded.json`
- `spike_03_references_sample_excluded.json`
- `spike_03_clangd_eval_summary.json`

Ground truth was checked with grep-style exact symbol search over source/header files, excluding comments and strings, then manually classifying same-entity matches vs text-only overcounts from overloads, macros, or repeated method names.

## Startup / Indexing / Memory

| Check | Result |
|---|---:|
| clangd initialize | 0.002 s |
| background index progress observed | yes |
| background index completion observed | yes |
| background index elapsed | 37.763 s |
| total LSP run elapsed | 52.094 s |
| peak RSS | 3573.2 MB |
| memory gate | PASS: < 4096 MB |

Indexing is under the 5 minute S0-03 gate. Peak RSS is below 4 GB, but close enough that Sprint 2b should keep the configured `memory_limit_mb: 4096` meaningful rather than decorative.

## Accuracy Summary

| Query | Pass | Total | Accuracy | Gate |
|---|---:|---:|---:|---|
| `textDocument/definition` | 50 | 50 | 100.0% | PASS: >= 90% |
| `textDocument/references` | 27 | 30 | 90.0% | PASS: >= 85% |

Definition counting accepts grep-confirmed semantic declaration/definition/macro-definition targets. For C++ split declaration/implementation cases, clangd may return the canonical declaration when queried from an implementation location; those were counted as correct when the target belonged to the same semantic symbol and grep confirmed the declaration/definition pair.

Reference counting uses manual same-entity classification. Exact text grep counts are listed, but they are not treated as required equality because simple grep overcounts common method names, overload families, macro occurrences, and unrelated same-spelling identifiers.

## Definition Sample Table

| # | Symbol | Query | Ground truth | clangd | Status |
|---|---|---|---|---|---|
| 1 | `WriteEmail` | `src/server/pkginfo_internal.cc:520` | `src/common/pkgmgr_info_handle_writer.hh:121` | `src/common/pkgmgr_info_handle_writer.hh:121` | PASS |
| 2 | `GetInt` | `src/server/database/query_handler.cc:220` | `src/server/database/query_handler.hh:48` | `src/server/database/query_handler.hh:48` | PASS |
| 3 | `RemovablePkgFilterChecker` | `src/common/filter_checker/filter_checker_provider.cc:46` | `src/common/filter_checker/pkg_filter_checker/removable_pkg_filter_checker.hh:26` | `src/common/filter_checker/pkg_filter_checker/removable_pkg_filter_checker.hh:26` | PASS |
| 4 | `CacheFlag` | `src/server/database/cache_db_handler.cc:85` | `src/server/cache_flag.hh:29` | `src/server/cache_flag.hh:29` | PASS |
| 5 | `CheckFilter` | `src/common/filter_checker/app_filter_checker/category_app_filter_checker.hh:30` | `src/common/filter_checker/app_filter_checker/category_app_filter_checker.hh:30` | `src/common/filter_checker/app_filter_checker/category_app_filter_checker.hh:30` | PASS |
| 6 | `GetOpType` | `src/common/parcel/query_parcelable.cc:111` | `src/common/parcel/query_parcelable.hh:33` | `src/common/parcel/query_parcelable.hh:33` | PASS |
| 7 | `GetUseSystemCerts` | `src/common/pkgmgr_info_handle.hh:507` | `src/common/pkgmgr_info_handle.cc:263` | `src/common/pkgmgr_info_handle.cc:263` | PASS |
| 8 | `DbException` | `src/server/initialize_db_internal.cc:156` | `/usr/include/tizen-database/database.hpp:56` | `/usr/include/tizen-database/database.hpp:56` | PASS |
| 9 | `ExtractResult` | `src/server/request_handler/remove_all_cache_request_handler.cc:29` | `src/server/request_handler/remove_all_cache_request_handler.hh:24` | `src/server/request_handler/remove_all_cache_request_handler.hh:24` | PASS |
| 10 | `Src` | `src/common/pkgmgr_info_handle.cc:162` | `src/common/pkgmgr_info_handle.hh:260` | `src/common/pkgmgr_info_handle.hh:260` | PASS |
| 11 | `GetHandleSize` | `src/server/shared_memory/shm_writer.hh:84` | `src/server/shared_memory/shm_writer.cc:461` | `src/server/shared_memory/shm_writer.cc:461` | PASS |
| 12 | `XHDPI` | `src/server/pkginfo_internal.cc:55` | `src/server/pkginfo_internal.cc:55` | `src/server/pkginfo_internal.cc:55` | PASS |
| 13 | `InsertMetadataInfo` | `src/server/pkginfo_internal.cc:1763` | `src/server/pkginfo_internal.cc:1403` | `src/server/pkginfo_internal.cc:1403` | PASS |
| 14 | `IAppFilterChecker` | `src/common/filter_checker/app_filter_checker_base.hh:29` | `src/common/filter_checker/app_filter_checker_base.hh:29` | `src/common/filter_checker/app_filter_checker_base.hh:29` | PASS |
| 15 | `PkgIdPkgFilterChecker` | `src/common/filter_checker/pkg_filter_checker/pkgid_pkg_filter_checker.hh:26` | `src/common/filter_checker/pkg_filter_checker/pkgid_pkg_filter_checker.hh:26` | `src/common/filter_checker/pkg_filter_checker/pkgid_pkg_filter_checker.hh:26` | PASS |
| 16 | `GetLock` | `src/server/shared_memory/shm_writer.cc:466` | `src/server/shared_memory/shm_writer.hh:66` | `src/server/shared_memory/shm_writer.hh:66` | PASS |
| 17 | `GetIndicatorDisplay` | `src/common/pkgmgr_info_handle.hh:646` | `src/common/pkgmgr_info_handle.cc:358` | `src/common/pkgmgr_info_handle.cc:358` | PASS |
| 18 | `Href` | `src/common/filter_checker/pkg_filter_checker/author_href_pkg_filter_checker.cc:27` | `src/common/pkgmgr_info_handle.cc:171` | `src/common/pkgmgr_info_handle.cc:171` | PASS |
| 19 | `GetCscPath` | `src/common/pkgmgr_info_handle.cc:254` | `src/common/pkgmgr_info_handle.hh:498` | `src/common/pkgmgr_info_handle.hh:498` | PASS |
| 20 | `TryConnection` | `src/common/socket/client_socket.hh:32` | `src/common/socket/client_socket.hh:32` | `src/common/socket/client_socket.hh:32` | PASS |
| 21 | `CreateParcel` | `src/server/request_handler/get_cert_request_handler.cc:23` | `src/common/parcel/parcelable_factory.cc:45` | `src/common/parcel/parcelable_factory.cc:45` | PASS |
| 22 | `Result` | `src/server/pkginfo_internal.cc:84` | `/usr/include/tizen-database/database.hpp:432` | `/usr/include/tizen-database/database.hpp:432` | PASS |
| 23 | `ROAppInfoParcelable` | `src/common/parcel/ro_appinfo_parcelable.cc:38` | `src/common/parcel/ro_appinfo_parcelable.hh:19` | `src/common/parcel/ro_appinfo_parcelable.hh:19` | PASS |
| 24 | `ReadString` | `src/common/parcel/command_parcelable.cc:56` | `/usr/include/parcel/parcel.hh:346` | `/usr/include/parcel/parcel.hh:346` | PASS |
| 25 | `GetCert` | `src/server/certinfo_internal.cc:188` | `src/server/certinfo_internal.cc:94` | `src/server/certinfo_internal.cc:94` | PASS |
| 26 | `Check` | `src/common/ready_checker.cc:48` | `src/common/ready_checker.cc:37` | `src/common/ready_checker.cc:37` | PASS |
| 27 | `Appid` | `src/common/pkgmgrinfo_pkginfo.cc:1522` | `src/common/pkgmgr_info_handle.cc:195` | `src/common/pkgmgr_info_handle.cc:195` | PASS |
| 28 | `GetUid` | `src/server/request_handler/set_pkginfo_request_handler.cc:43` | `src/common/parcel/abstract_parcelable.cc:148` | `src/common/parcel/abstract_parcelable.cc:148` | PASS |
| 29 | `Uri` | `src/common/pkgmgr_info_handle.hh:220` | `src/common/pkgmgr_info_handle.cc:151` | `src/common/pkgmgr_info_handle.cc:151` | PASS |
| 30 | `WriteToParcel` | `src/common/parcel/depinfo_parcelable.cc:59` | `src/common/parcel/depinfo_parcelable.hh:27` | `src/common/parcel/depinfo_parcelable.hh:27` | PASS |
| 31 | `ShmError` | `src/common/shared_memory/shm_config.cc:612` | `src/common/shared_memory/shm_config.hh:37` | `src/common/shared_memory/shm_config.hh:37` | PASS |
| 32 | `GetOnboot` | `src/common/pkgmgrinfo_appinfo.cc:1496` | `src/common/pkgmgr_info_handle.cc:372` | `src/common/pkgmgr_info_handle.cc:372` | PASS |
| 33 | `HandleRequest` | `src/server/request_handler/query_request_handler.cc:21` | `src/server/request_handler/query_request_handler.hh:22` | `src/server/request_handler/query_request_handler.hh:22` | PASS |
| 34 | `LOG` | `src/server/database/create_db_handler.cc:49` | `src/utils/logging.hh:90` | `src/utils/logging.hh:90` | PASS |
| 35 | `Author` | `src/common/pkgmgr_info_handle.cc:170` | `src/common/pkgmgr_info_handle.hh:277` | `src/common/pkgmgr_info_handle.hh:277` | PASS |
| 36 | `CheckFilter` | `src/common/filter_checker/pkg_filter_checker/preload_pkg_filter_checker.hh:30` | `src/common/filter_checker/pkg_filter_checker/preload_pkg_filter_checker.cc:21` | `src/common/filter_checker/pkg_filter_checker/preload_pkg_filter_checker.cc:21` | PASS |
| 37 | `BUFSIZE` | `src/server/pkginfo_internal.cc:1442` | `src/common/pkgmgrinfo_private.h:68` | `src/common/pkgmgrinfo_private.h:68` | PASS |
| 38 | `ResetPriority` | `src/server/request_handler/create_cache_request_handler.hh:36` | `src/server/request_handler/create_cache_request_handler.cc:31` | `src/server/request_handler/create_cache_request_handler.cc:31` | PASS |
| 39 | `WriteIsDisabled` | `src/common/pkgmgr_info_handle_writer.cc:950` | `src/common/pkgmgr_info_handle_writer.hh:486` | `src/common/pkgmgr_info_handle_writer.hh:486` | PASS |
| 40 | `WriteAppSetting` | `src/server/pkginfo_internal.cc:492` | `src/common/pkgmgr_info_handle_writer.cc:542` | `src/common/pkgmgr_info_handle_writer.cc:542` | PASS |
| 41 | `InstallLocationPkgFilterChecker` | `src/common/filter_checker/filter_checker_provider.cc:34` | `src/common/filter_checker/pkg_filter_checker/install_location_pkg_filter_checker.hh:26` | `src/common/filter_checker/pkg_filter_checker/install_location_pkg_filter_checker.hh:26` | PASS |
| 42 | `Init` | `src/common/shared_memory/shm_app_reader.hh:33` | `src/common/shared_memory/shm_app_reader.cc:237` | `src/common/shared_memory/shm_app_reader.cc:237` | PASS |
| 43 | `AppInfoHandleView` | `src/common/filter_checker/app_filter_checker/ui_gadget_app_filter_checker.hh:31` | `src/common/pkgmgr_info_handle.hh:620` | `src/common/pkgmgr_info_handle.hh:620` | PASS |
| 44 | `SetShmStatus` | `src/common/shared_memory/shm_config.hh:131` | `src/common/shared_memory/shm_config.cc:668` | `src/common/shared_memory/shm_config.cc:668` | PASS |
| 45 | `GetExec` | `src/common/pkgmgr_info_handle.hh:633` | `src/common/pkgmgr_info_handle.cc:345` | `src/common/pkgmgr_info_handle.cc:345` | PASS |
| 46 | `AppInfoHandleView` | `src/common/filter_checker/app_filter_checker/auto_restart_app_filter_checker.hh:31` | `src/common/pkgmgr_info_handle.hh:620` | `src/common/pkgmgr_info_handle.hh:620` | PASS |
| 47 | `Orientation` | `src/common/pkgmgrinfo_appinfo.cc:1379` | `src/common/pkgmgr_info_handle.cc:165` | `src/common/pkgmgr_info_handle.cc:165` | PASS |
| 48 | `Execute` | `src/server/database/create_db_handler.hh:42` | `src/server/database/create_db_handler.cc:45` | `src/server/database/create_db_handler.cc:45` | PASS |
| 49 | `ReadPermission` | `src/common/parcel/appinfo_parcelable.cc:250` | `src/common/parcel/appinfo_parcelable.hh:54` | `src/common/parcel/appinfo_parcelable.hh:54` | PASS |
| 50 | `CheckFilter` | `src/common/shared_memory/shm_app_reader.cc:283` | `src/common/filter_checker/app_filter_checker_base.hh:30` | `src/common/filter_checker/app_filter_checker_base.hh:30` | PASS |

## References Sample Table

| # | Symbol | Query | Ground truth | clangd | Status / case |
|---|---|---|---|---|---|
| 1 | `ExecAppFilterChecker` | `src/common/filter_checker/app_filter_checker/exec_app_filter_checker.hh:26` | grep-confirmed semantic refs; text_grep=5 | 5 refs | PASS |
| 2 | `GetResControl` | `src/common/pkgmgrinfo_appinfo.cc:1399` | grep-confirmed semantic refs; text_grep=7 | 4 refs | PASS |
| 3 | `COMMAND` | `src/common/request_type.hh:38` | grep-confirmed semantic refs; text_grep=5 | 4 refs | PASS |
| 4 | `ERROR` | `src/server/request_handler/create_db_request_handler.cc:38` | grep-confirmed semantic refs; text_grep=146 | 0 refs | FAIL: macro_arg_level_token |
| 5 | `WritePackageSystem` | `src/common/pkgmgr_info_handle_writer.cc:1089` | grep-confirmed semantic refs; text_grep=4 | 4 refs | PASS |
| 6 | `API` | `src/common/pkgmgrinfo_plugininfo.cc:25` | grep-confirmed semantic refs; text_grep=329 | 240 refs | PASS |
| 7 | `CreateSharedMemory` | `src/server/database/cache_db_handler.cc:73` | grep-confirmed semantic refs; text_grep=7 | 3 refs | PASS |
| 8 | `NONE` | `src/common/shared_memory/shm_config.cc:591` | grep-confirmed semantic refs; text_grep=102 | 85 refs | PASS |
| 9 | `SocketActivator` | `src/common/pkgmgrinfo_pkginfo.cc:1335` | grep-confirmed semantic refs; text_grep=14 | 14 refs | PASS |
| 10 | `GetData` | `src/common/parcel/ro_appinfo_parcelable.cc:50` | grep-confirmed semantic refs; text_grep=37 | 6 refs | PASS |
| 11 | `ROAppInfoParcelable` | `src/common/parcel/parcelable_factory.cc:97` | grep-confirmed semantic refs; text_grep=16 | 16 refs | PASS |
| 12 | `ERROR` | `src/server/request_handler/query_request_handler.cc:28` | grep-confirmed semantic refs; text_grep=146 | 0 refs | FAIL: macro_arg_level_token |
| 13 | `GetMainApp` | `src/common/pkgmgr_info_handle.cc:354` | grep-confirmed semantic refs; text_grep=5 | 5 refs | PASS |
| 14 | `AppInfoHandleContainer` | `src/server/database/appinfo_db_handler.cc:38` | grep-confirmed semantic refs; text_grep=25 | 25 refs | PASS |
| 15 | `WriteTepName` | `src/server/appinfo_internal.cc:572` | grep-confirmed semantic refs; text_grep=8 | 4 refs | PASS |
| 16 | `SetQueryArgs` | `src/server/database/query_handler.cc:214` | grep-confirmed semantic refs; text_grep=8 | 8 refs | PASS |
| 17 | `GetRequestResult` | `src/common/parcel/abstract_parcelable.cc:154` | grep-confirmed semantic refs; text_grep=8 | 8 refs | PASS |
| 18 | `WriteForAllUsers` | `src/common/pkgmgr_info_handle_writer.cc:705` | grep-confirmed semantic refs; text_grep=8 | 4 refs | PASS |
| 19 | `Check` | `src/common/shared_memory/shm_app_reader.cc:144` | grep-confirmed semantic refs; text_grep=13 | 5 refs | PASS |
| 20 | `WriteAliasAppid` | `src/common/pkgmgr_info_handle_writer.cc:1078` | grep-confirmed semantic refs; text_grep=3 | 3 refs | PASS |
| 21 | `Detach` | `src/common/pkgmgr_info_handle_writer.cc:1114` | grep-confirmed semantic refs; text_grep=13 | 4 refs | PASS |
| 22 | `CreateParcel` | `src/server/request_handler/create_db_request_handler.cc:26` | grep-confirmed semantic refs; text_grep=20 | 20 refs | PASS |
| 23 | `GetHandles` | `src/common/shared_memory/shm_app_reader.hh:26` | grep-confirmed semantic refs; text_grep=52 | 5 refs | PASS |
| 24 | `ReadFromParcel` | `src/common/parcel/ro_pkginfo_parcelable.hh:27` | grep-confirmed semantic refs; text_grep=36 | 16 refs | PASS |
| 25 | `PkgInfoIndex` | `src/common/pkgmgr_info_handle.cc:212` | grep-confirmed semantic refs; text_grep=6 | 6 refs | PASS |
| 26 | `LOGE` | `src/common/system_locale.cc:75` | grep-confirmed semantic refs; text_grep=347 | 345 refs | PASS |
| 27 | `WARNING` | `src/common/socket/server_socket.cc:48` | grep-confirmed semantic refs; text_grep=28 | 0 refs | FAIL: macro_arg_level_token |
| 28 | `LOG` | `src/server/database/depinfo_db_handler.cc:46` | grep-confirmed semantic refs; text_grep=193 | 191 refs | PASS |
| 29 | `PluginWriter` | `src/common/pkgmgr_info_handle_writer.hh:223` | grep-confirmed semantic refs; text_grep=24 | 24 refs | PASS |
| 30 | `WriteIsPackageDisabled` | `src/server/appinfo_internal.cc:622` | grep-confirmed semantic refs; text_grep=3 | 3 refs | PASS |

## Miss / Mismatch Cases

Definition misses: none.

Reference misses:

| # | Symbol | Query | Type | Notes |
|---|---|---|---|---|
| 4 | `ERROR` | `src/server/request_handler/create_db_request_handler.cc:38` | macro argument token | `LOG(LEVEL)` token-pastes `LEVEL` into `LOG_##LEVEL`; clangd returns no references for the `ERROR` argument token. |
| 12 | `ERROR` | `src/server/request_handler/query_request_handler.cc:28` | macro argument token | Same `LOG(ERROR)` case as #4. |
| 27 | `WARNING` | `src/common/socket/server_socket.cc:48` | macro argument token | Same logging macro argument pattern with `LOG(WARNING)`. |

These misses are edge cases in macro argument tokens, not normal function/class/type lookup failures. The `LOG` macro itself was correctly resolved in both definition and references samples.

Sprint 1+ implementation note: clangd 对 token-paste 宏参数的 references 不可靠 -> CNEI 实现时，宏展开相关 symbol 的 references 应标 `confidence: low/medium`，并在 `negative_fact` 注明可能不完整。

## mtime Basic Probe

S0-03 only checks that compile database mtime is readable and comparable with CMake inputs.

| Item | Value |
|---|---|
| `compile_commands.json` mtime | `2026-05-28T14:43:50.816932` |
| newest `CMakeLists.txt` | `tool/CMakeLists.txt` |
| newest `CMakeLists.txt` mtime | `2026-05-28T14:05:30.146986` |
| CMakeLists count | 8 |
| basic stale result | `false` |

Full stale scenario construction and confidence downgrading remain S0-09 scope.

## Conclusion

S0-03 PASS.

| Acceptance | Result | Evidence |
|---|---|---|
| clangd starts within 5 min | PASS | initialize 0.002 s |
| indexing completes within 5 min | PASS | background index completion observed at 37.763 s |
| memory peak < 4 GB | PASS | 3573.2 MB |
| definition accuracy >= 90% | PASS | 50/50 = 100.0% |
| references accuracy >= 85% | PASS | 27/30 = 90.0% |
| stale basic mtime probe | PASS | compile DB mtime readable; current DB newer than all `CMakeLists.txt` |

## Follow-up Notes

- clangd is viable for the Phase 1A `cmake_ninja` path on `pkgmgr-info`.
- Macro argument tokens such as `LOG(ERROR)` should be treated as known lower-confidence reference edge cases in CNEI; normal macro names such as `LOG` and `LOGE` resolved successfully.
- Peak RSS is below the current 4 GB gate but close enough that production integration should enforce the CNEI memory limit and preserve degraded-backend fallback behavior.
