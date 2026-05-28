# S0-10 Scale Feasibility Spike（OS 级规模可行性验证）

**版本**：v1.0
**所属**：Phase 1A Sprint 0（独立 spike，可与 S0-01 ~ S0-09 并行或后置）
**性质**：可行性验证，**不写产品代码**
**关联**：《ADR-001 CNEI Scale Direction》
**前置**：已读 ADR-001

---

## 0. 这个 spike 的目的

ADR-001 决定了 CNEI 三层架构（Layer 0 Migration Intelligence + Layer 1 RPM Semantic + Layer 2 Live）。但整个 Layer 0/1 方案建立在几个**未验证的工程假设**上，其中 P0 项是**生死线**——任一 FAIL 则整个 Layer 1 scip-clang 方案要重新评估。

**S0-10 的目标**：用真实 Tizen RPM 验证这些假设，产出**真实数据**，供 CNEI v0.4 定稿。

**关键原则**：

- 先验证生死线（P0），生死线挂了后面全白做
- 用真实 musl/libc++ 编译错误，不是"能跑通"的玩具代码
- 不追求产品化，只追求"能不能做 / 哪条路最稳"的结论

---

## 1. 规模与时间盒

- **RPM 样本**：50-100 个（不是 200 起步），覆盖：
  - 小型 C 库
  - 中型 C++ 库
  - 带 generated headers 的包
  - **至少 1 个使用 PCH 的包**（验证 scip-clang PCH 限制）
  - 至少 1 个 provider + 多个 consumer（验证 cascade failure）
- **时间盒**：建议 1-2 周（如果资源允许可与主线 Sprint 0 并行）
- **超时处理**：P0 必须完成；P1 尽量完成；P2 可推迟到 Phase 1.5 前

---

## 2. P0：生死线（必须 PASS，否则方案重评估）

### P0-1: gbs build command extraction

**目标**：验证能否为真实 Tizen RPM 捕获完整构建命令。

**捕获内容**（ChatGPT 扩展：不只 compile，还要 link + artifact）：

- compile command
- **link command**（LLD 迁移核心）
- sysroot
- toolchain wrapper（CC/CXX/LD 实际调用）
- generated headers path
- include path / defines / flags

**方法**（试三种，对比哪种稳）：

```
方法 1: intercept-build (bear / scan-build) wrap 编译器
方法 2: wrapper CC/CXX/LD，把真实命令落日志
方法 3: 解析 gbs build log（后处理）
```

**Acceptance**：

- [ ] 至少一种方法对 3 类 RPM（C 库 / C++ 库 / generated headers 包）都能捕获 compile + link command
- [ ] sysroot / toolchain wrapper / generated headers path 完整

**判定**：
- PASS：≥ 1 种方法对 3 类 RPM 都能捕获完整命令
- PARTIAL：部分 RPM 可用，需 workaround
- FAIL：全部方法不可行 → **Layer 1 方案重评估**

**Deliverable**：`spike_reports/s0_10_p0_1_gbs_extraction.md` + 样本 compile/link command（脱敏）

---

### P0-2: chroot path mapping（生死线中的生死线，Kimi 致命发现）

**目标**：验证 gbs chroot 内的路径能否在宿主机被 scip-clang 解析。

**问题**：gbs 在 chroot 内构建，compile_commands.json 路径是 chroot 内绝对路径（`/builddir/build/BUILD/...`），宿主机上可能不存在。

**三种解法对比**（ChatGPT 修正 3：不只验证能否用，要对比哪个最稳）：

```
方案 A: 在同一 gbs chroot 内运行 indexer
  优点: 路径天然有效
  缺点: indexer/toolchain 要装进 chroot，集成复杂
  验证: chroot 内有无 Clang 16+；scip-clang 能否在 chroot 内跑

方案 B: 导出 chroot rootfs，host 侧 path remap
  /builddir/build/BUILD/pkg → /host/exported_chroot/builddir/build/BUILD/pkg
  验证: source path / generated headers / sysroot / toolchain wrapper /
        relative include / absolute include 是否都能 remap

方案 C: 重写 compile_commands.json（chroot 路径 rewrite 成 host 路径）
  rewrite: directory / file / arguments 中的 -I /builddir/... / --sysroot /...
  最灵活，但最容易漏
```

**Acceptance**：

- [ ] 三种方案各跑一遍，记录哪个能让 scip-clang 解析到 source / header / sysroot
- [ ] 明确哪个最稳、哪个有什么坑

**判定**：
- PASS：≥ 1 种方案能让 scip-clang 完整解析路径
- PARTIAL：能解析但有遗漏（如 generated headers 漏）
- FAIL：三种都不通 → **Layer 1 scip-clang 方案报废，重新设计**

**Deliverable**：`spike_reports/s0_10_p0_2_chroot_path.md` + 三方案对比表

---

### P0-3: artifact symbol index 数据源确认

**目标**：确认能否获取 RPM 二进制产物的符号表（artifact symbol index 是 Layer 0 主数据源）。

**采集内容**：

- defined / undefined symbols
- weak / strong
- visibility（hidden / default）
- versioned symbol
- SONAME / owning RPM

**方法**（两条路）：

```
路径 1: build 后立刻从 build artifacts 提取
  - ~/GBS-ROOT/local/BUILD/ 下的 .o / .so / .a 是否存在？
  - nm / readelf / llvm-readobj 能否提取？

路径 2: 从 RPM 包提取
  - rpm2cpio + cpio -idmv
  - 对提取出的 .so / .a 运行 nm
```

**Acceptance**：

- [ ] 至少一种方法能稳定获取 ≥ 80% RPM 的符号表
- [ ] 能回答"某 undefined symbol 由哪个 .so/.a 提供"

**判定**：
- PASS：≥ 1 种方法稳定获取 80%+ RPM 符号表
- PARTIAL：需额外步骤（如改 gbs 配置保留 build artifacts）
- FAIL：无法获取 → artifact symbol index 无法实现，Layer 0 主数据源缺失

**Deliverable**：`spike_reports/s0_10_p0_3_artifact_symbols.md`

---

## 3. P1：架构边界（决定 Layer 1 取舍）

### P1-1: diagnostic fingerprint clustering

**目标**：验证能否用简单规则对真实编译错误聚类，并区分 primary/cascade。

**方法**：

```
a) 收集 50-100 个真实 Tizen 编译错误日志（含 musl/libc++ 迁移错误）
b) 用正则提取 error message pattern（如 "undefined reference to XXX"）
c) 用 symbol name + error type 做简单聚类
d) ★ 初步识别 primary vs cascade failure（ChatGPT 盲点）：
   - provider 包失败 → consumer 的 undefined reference 是 cascade
   - 需要结合 P0-3 artifact symbol + package dependency 判断
e) 人工标注"是否同一根因"，计算聚类准确率
```

**Acceptance**：

- [ ] 聚类准确率 ≥ 80%
- [ ] 能初步区分 primary failure 和 cascade failure

**判定**：PASS ≥ 80% / PARTIAL 60-80% / FAIL < 60%

**Deliverable**：`spike_reports/s0_10_p1_1_clustering.md` + 聚类结果样本

---

### P1-2: scip-clang current-package shard 策略验证

**目标**：验证 scip-clang "只持久化 package-owned facts" 策略 + 二次方成本 + PCH 限制。

**方法**：

```
a) 选一个依赖基础库（如 musl）的 RPM
b) 用 P0-2 确定的路径方案，生成 compilation database
c) 运行 scip-clang，只持久化 package-owned facts（允许解析依赖 header）
d) 观察:
   - 能否成功索引？
   - 本地符号精度 ≥ 90%？
   - 跨包符号跳转失效方式（预期失效，确认怎么失效）

e) ★ 二次方成本验证（ChatGPT 修正 2，写成假设验证）:
   - 同一基础库 header 在 20/50/100 个 RPM 中被重复解析的次数
   - 总索引时间随 RPM 数：线性 / 超线性 / 接近二次？

f) ★ PCH 验证（Kimi 盲点）:
   - 故意选一个使用 PCH 的 RPM
   - 测 scip-clang 能否索引
   - 如失败，记录"该类 RPM 降级为纯 Layer 0 + Layer 2"
```

**Acceptance**：

- [ ] 能成功索引当前包，本地符号精度 ≥ 90%
- [ ] 二次方成本有真实数据（线性/超线性/二次）
- [ ] PCH RPM 行为明确（支持 or 降级）

**判定**：PASS（精度 ≥ 90% 且成本可接受）/ PARTIAL（精度 < 90% 或成本偏高）/ FAIL（无法索引）

**Deliverable**：`spike_reports/s0_10_p1_2_scip_clang.md` + 索引时间/内存/精度数据

---

### P1-3: ClusterEvidencePacket exemplar strategy

**目标**：验证 cluster 选 exemplar 的策略可行。

**方法**：

```
对 P1-1 聚出的 cluster，每个选 3 类 exemplar：
1. smallest failing package（最小复现）
2. most common failure pattern package（最典型）
3. highest impact / most depended-on package（最高影响，需 package dep graph）

验证：这 3 类 exemplar 能否代表整个 cluster 的修复需求
```

**Acceptance**：

- [ ] 能为每个 cluster 选出 3 类 exemplar
- [ ] exemplar 的修复方案能推广到 cluster 其他成员（抽样验证）

**判定**：PASS / PARTIAL / FAIL

**Deliverable**：`spike_reports/s0_10_p1_3_exemplar.md` + ClusterEvidencePacket 样本

---

## 4. P2：性能与增强（可 PARTIAL，可推迟）

### P2-1: tree-sitter/ctags global source identifier index

**目标**：验证 Layer 0 recall 层的速度/存储/误召回率。

**方法**：

```
a) 对 10 个 RPM 源码跑 tree-sitter 提取 identifier
b) 写入 SQLite，测:
   - 提取时间 / 1000 行
   - 存储大小 / 1000 行
   - 查询延迟（按 identifier 查）
   - ★ 误召回率（recall 层只做候选，要知道噪声多大）
```

**Acceptance**：
- [ ] 提取 < 1s/1000 行，查询 < 100ms，存储 < 1MB/1000 行
- [ ] 误召回率有数据（明确这是 recall 不是 truth）

**判定**：PASS / PARTIAL

**Deliverable**：`spike_reports/s0_10_p2_1_treesitter.md`

---

### P2-2: storage benchmark

**目标**：验证存储选型（SQLite → DuckDB）+ 分区策略。

**方法**：

```
a) SQLite 写入/查询 benchmark（50-100 RPM 的 diagnostics + artifact symbols）
b) DuckDB 聚类查询 benchmark（同样数据，OLAP 型查询）
c) ★ 验证分区策略（ChatGPT 修正 4）:
   - 按 toolchain_profile / arch / package / build_id 分区
   - artifact symbols 和 diagnostics 分表
d) 数据规模估算（外推到数千 RPM 的存储大小，验证是否真 GB 级 or 上百 GB）
```

**Acceptance**：
- [ ] SQLite 写入/查询性能可接受
- [ ] DuckDB 聚类查询明显快于 SQLite（验证 OLAP 价值）
- [ ] 数据规模外推有数据

**判定**：PASS / PARTIAL

**Deliverable**：`spike_reports/s0_10_p2_2_storage.md`

---

## 5. S0-10 Gate 决策

```
P0 全 PASS → Layer 1 scip-clang 方案可行，继续 Phase 1.5 规划
P0 任一 FAIL → Layer 1 scip-clang 方案重评估:
   - chroot 路径不通（P0-2 FAIL）→ 考虑 chroot 内运行 indexer 或放弃 scip-clang
   - artifact 拿不到（P0-3 FAIL）→ Layer 0 主数据源重新设计
P1 决定架构边界（精度/成本/PCH 取舍）
P2 决定性能优化方向（可推迟）
```

**S0-10 结论直接输入 CNEI v0.4 定稿。**

---

## 6. Deliverable 汇总

```
docs/dev_memory/phase_1a/sprint_0_spike/scale_spike/
├── s0_10_summary.md                    # 汇总 P0/P1/P2 结论 + Gate 决策
├── spike_reports/
│   ├── s0_10_p0_1_gbs_extraction.md
│   ├── s0_10_p0_2_chroot_path.md       # 生死线中的生死线
│   ├── s0_10_p0_3_artifact_symbols.md
│   ├── s0_10_p1_1_clustering.md
│   ├── s0_10_p1_2_scip_clang.md
│   ├── s0_10_p1_3_exemplar.md
│   ├── s0_10_p2_1_treesitter.md
│   └── s0_10_p2_2_storage.md
├── data/                               # 真实样本数据（脱敏）
└── adrs/                               # 如有 PARTIAL/FAIL 决策
```

---

## 7. 与主线 Sprint 0 的关系

- S0-10 是**独立 spike**，验证 OS 级规模可行性
- 不阻塞 S0-01 ~ S0-09（主线 Phase 1A Live CNEI 验证）
- 可并行或后置（资源允许就并行）
- S0-10 结论用于 Phase 1.5 规划，不影响 Phase 1A 主线进 Sprint 1

---

**S0-10 Scale Feasibility Spike 任务定义结束。**
