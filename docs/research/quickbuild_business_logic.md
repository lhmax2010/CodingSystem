# Quickbuild 业务逻辑：只读调查

调查日期：2026-11-02（本地时区 Asia/Shanghai；构建页面时间按页面原文，不擅自换算）。

本报告区分公开 Tizen QuickBuild 的 **Tizen-Base-Toolchain/RBS/TRIGGER（配置 1917）**、相关 SBS/Unified 流水线，以及 VD Cosmos。它们不能仅因同用 QuickBuild 就共用字段或默认值。**已证实**指已有实测记录或此次只读证据支持的有限结论；**推断**指由证据推导但未经执行验证；**未知**指资料不足。设计裁定、测试夹具和客户端策略不作为服务端能力的证明。

此次未提交构建、未修改任何 QuickBuild 配置、未进入提交表单、未执行取消/停止/Accept/推广操作。登录在可见浏览器中由用户完成，没有在终端索取凭据。Cosmos 仅查仓库资料，没有访问其网站或 P4 服务。原始材料保存在被 `.gitignore` 覆盖的 `temp/`，仅本结论文档提交 Git。

## 资料范围与出处索引

以下缩写都是确定的本地路径或 Git 版本，不代表另一个网站：

- `L` = `/home/linhao/Toolchain/development/LogAnalysisSkill`。
- `T` = `/home/linhao/Toolchain/development/CodingSystem/temp/qb-research-20261102-LRD8cE`。网页正文是只读文本快照；JSON 是业务变量白名单摘录；`.log` 为页面提供的完整日志下载；HTML/XML/gzip 是下载站只读 GET 的原始响应正文。路径在本机有效，不随本报告进入 Git。
- `D` = `L/docs/clang-fix-campaign/p5q-qb-trigger-design-v1.8-FROZEN.md`。
- `E15` = `L/docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/progress.md`。
- `E20` = `L/docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger`。
- 上述 QuickBuild 主证据版本为 `clang-fix-campaign` / `origin/clang-fix-campaign`，提交 `accd7f4c24c8976ebb562b45ade9b82f1bc81bc3`；引用行号对应此版本。
- `C` = LogAnalysisSkill 的远端分支 `vd-cosmos-loganalyzer` 中 `docs/enhance/vd-cosmos-loganalyzer-hld-v0.9.4.md`，固定提交 `b6b7c094c1ed4fcd6b0c5d9b919a1bfb300636cd`。本地逐字副本为 `T/cosmos-hld-v0.9.4.md`，行号相同；只读 Git 副本为 `T/remote-cosmos.git`。下文 `C:行号` 均指该仓库文件，而非此次访问 Cosmos 的证据。

### 全部分支检索与复用

第二个候选仓库 `/home/toolchain/development/LogAnalysisSkill` 不存在。对 `L` 的所有本地 `refs/heads`、`refs/remotes` 共 135 个引用检索 QuickBuild/QB/Cosmos/BUILD_PKG_LIST/base URL/Base CL/shelve/RBS/SBS/TRIGGER：得到 6,586 条“引用:路径”，合并同名路径后 2,012 个文件。结果包含重复历史版本和测试，不等于 2,012 项独立事实。

另以 `git ls-remote --heads origin` 核对远端全部 55 个分支，发现本地唯一未同步的是 `vd-cosmos-loganalyzer`。将该分支单独浅克隆为 `T/remote-cosmos.git` 后检索，补充 2,162 条命中路径；没有切换或修改原仓库工作区。其余远端分支的 SHA 均与原本地远端引用一致。

完整路径与分支清单：`T/branch-heads.txt`、`T/all-branch-matching-paths.txt`、`T/remote-heads-at-research.txt`、`T/remote-cosmos-matching-paths.txt`（最后一个文件中的 `HEAD` 即上述 Cosmos 固定提交）。检索覆盖每个分支尖端的跟踪文本；未把未跟踪草稿或客户端测试输出升级成服务器事实。

| 路径（相对 L） | 分支 / 版本 | 复用要点 |
|---|---|---|
| `docs/clang-fix-campaign/p5q-qb-trigger-design-v1.8-FROZEN.md` | `clang-fix-campaign`、同名 origin 分支，`accd7f4` | RBS/SBS 区别、字段映射、父子关系、快照滚动、成功/失败及请求标记实测；需区分裁定与实测 |
| `docs/clang-fix-campaign/dev_memory/stage15_p1_ef_spike/progress.md` | 同上 | SBS 样本、RBS 表单标签/HTML name/默认值；`:877` 起字段表 |
| `docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/progress.md` | 同上 | `:5011` 起 Oct-19 成功样本、变量及 manifest 对照 |
| `docs/clang-fix-campaign/dev_memory/stage20_p5q_qb_trigger/evidence/C6b/` | 同上 | `configuration-1917.md`、`raw-active-01/`、`offline-analysis.json` 保存状态、请求标记和原始页面证据 |
| `tizen-ci-shared/scripts/tizen_ci_shared/quickbuild_http.py` | 同上 | `:106` 完整日志下载，`:150` Unified 包日志路径换算；只读代码，未执行 |
| `tizen-ci-triage/scripts/ci_triage/quickbuild_log.py` | 同上；main 历史也有 | `:19` 起解析日志 `build_pkg_list_dic` 的 repo→commit 映射 |
| `tizen-ci-triage/scripts/ci_triage/quickbuild.py`；`release-v1.4.0/tizen-ci-triage/scripts/ci_triage/quickbuild.py` | 本地 `main`=`18a970539d0cadad15913eee3b62cc79d5e974b1`；`origin/main`=`4f11764511acd12bddaee2be7762f2d9ceff8176` | 较早下载实现；采用新分支集中实现，不重复在线探测已确认路径 |
| `docs/enhance/vd-cosmos-loganalyzer-hld-v0.9.4.md` | `vd-cosmos-loganalyzer`，`b6b7c09` | `:175` 现行业务输入；`:337` 报告；`:490` Base CL/shelve；`:1434` 起既有只读侦察，保留未决问题 |
| `docs/enhance/dev_memory/STATUS.md`、`docs/enhance/batch1.1/DELIVERY.md`、`docs/enhance/batch2.1/evidence/` | 同上 | 读取端实现/离线验收与构建机验收的阶段记录；不能用离线夹具证明新的服务端行为 |
| `vd-cosmos-core/src/vd_cosmos_core/`、`vd-cosmos-fetch/`、`vd-cosmos-watch/`、`vd-cosmos-workflow/` | 同上 | Cosmos 读取与分析工具；配置、解析与状态机属于客户端实现，未运行其脚本 |

新增网页核对集中在已有资料不足的近期成功构建、源码与构建根快照关系、build.conf 元数据、下载保留政策和当前并发观察。原始材料来源映射见 `T/README.md`。

## Q1：每个包的代码版本由什么决定？不指定时怎样？

**结论：已证实（Tizen Base RBS 样本）；Live/Partial 的所有默认规则及 CL 机制不能由此外推。** 包源码清单、构建根二进制依赖仓库、build.conf 是不同输入。

| 输入 | 已有事实与边界 | 标注 / 证据 |
|---|---|---|
| Profile 快照 | 父构建 `BUILD_REFERENCE`、`SNAPSHOT_NUM` / `SNAPSHOT_NUM_URL` 选择源码清单所用快照。近期样本使用 `20261028.234757`，其原 manifest 有 250 个项目 | 已证实；`T/build-1213815-overview.txt:92`、`T/manifest-input-20261028.xml` |
| `BUILD_PKG_LIST` | 父/子变量页保存展开后的全量 `repo@commit`；不能把它与用户在表单输入的覆盖清单混为一谈 | 已证实；`D:36`、`D:37`；`T/build-1213815-variables.json`、`T/build-1213816-variables.json` |
| `BUILD_PKG_LIST_MODIFY` | 表单 **Build Package List** 对应父构建此变量，作用是给目标包指定提交。历史样本覆盖一条 libtirpc，另外仍有全量包清单 | 已证实；`D:1110`、`D:1126`，`E20/progress.md:5019` |
| ADD / RM | 表单分别为 **Add Package List** / **Remove Package List**；回显变量 `BUILD_PKG_LIST_ADD` / `BUILD_PKG_LIST_RM`。近期样本 MODIFY 为空，ADD 为一条 vtable-dumper，输出清单恰为输入 250 条加该条，其他 revision 未变。RM 的边界与冲突优先级没有此次实测 | ADD 已证实；RM 字段已证实、执行细节未知；`E15:887`、`T/comparison.json`、父变量 JSON |
| base 快照 URL | 决定构建根依赖仓库，不等于每个待构建包的 Git revision。样本父 overview 的 Base URL 是 `/reference`；子日志把它解析为 `20261013.024319/repos/standard` 并写进 `.gbs.conf` 的活动 base/debug 仓库 | 已证实；`T/build-1213815-overview.txt:94`；`T/build-1213816.log:309` 起 |
| Base CL / shelve CL | 在公开 Tizen 此配置的表单、变量和既有记录中，未确认与 VD 相同的 P4 输入机制。VD 的 `PACKAGE_LIST` / `SHELVE_LIST` 则有既有证据，见 Q7；不能将 CL 当作 Git commit | Tizen 未知；VD 部分已证实；`E15:877`、`C:490`、`C:1448` |

**未显式指定时：** 历史 RBS 表单默认 `BUILD_TYPE=Full`、`REPO_TYPE=ALL`、`BUILD_REFERENCE=Ref. Snapshot`、`PROJECT_BRANCH=tizen_base`，Build/Add/Remove 三个文本区为空，参考快照下拉只提供当时 reference；`FAIL_FAST` 勾选。证据 `E15:879` 起、`D:78`。这只能证明取证时配置的默认，不代表所有工程永远相同。

近期成功样本验证了“MODIFY 留空时，未新增的包保留所选 Profile manifest 的 revision”，**没有验证完全空白的 Live/Partial 提交、缺省 commit、重复 repo、ADD/MODIFY/RM 冲突的服务器处理**。未给 build.conf 时实际仍有配置/脚本生成的 `./build.conf`，但其全部生成优先级未知（Q3）。

SBS 另有约束：站点指南称 SBS 固定使用 Reference，除 Build/Add/Remove 包清单外，Child configurations、Build reference、TARGET_IMAGE 等为固定值（`T/quickbuild-user-guide.txt:33` 起）。这是指南陈述，不把 RBS 的可选项套到 SBS；Unified 与 Base 的架构组织和 FAIL_FAST 也有已知差别（`D:72`）。

## Q2：怎样显式指定 base、每包版本和 build.conf？

**结论：包 Git commit 与 Profile 快照的输入字段已证实；独立固定构建根 base 和 build.conf 的可写提交字段未知。**

| 意图 | 字段 / 变量 | 可确认到什么程度 |
|---|---|---|
| 选择 Profile 历史快照 | `BUILD_REFERENCE=Snapshot Number` + `SNAPSHOT_NUM`；另有 `PROJECT_BRANCH` | 选项存在，且成功样本父构建确为此模式，值为 `20261028.234757`；未重新填表，也未验证历史选项全部可选 |
| 固定每个已有包 Git 提交 | **Build Package List**，一行 `仓库路径@完整commit`；父回显 `BUILD_PKG_LIST_MODIFY` | 既有真实提交及回显已证实；全量展开结果需读 `BUILD_PKG_LIST` |
| 增减包 | **Add Package List** / **Remove Package List**；回显 `BUILD_PKG_LIST_ADD` / `BUILD_PKG_LIST_RM` | 字段已证实；ADD 有近期实际输出对照，RM 的格式/执行边界未补测 |
| 独立固定构建根 base | 读到 `BASE_URL_NUM=reference`、`BASE_PATH_URL`、overview 的 **Base URL**；日志有 `base_path_url` | 这些读回变量/脚本变量的存在不证明用户可在每次提交中写入。历史十三标签表单没有独立 base URL 项；不能用 `SNAPSHOT_NUM` 替代这个保证 |
| 固定 build.conf | 读到 `BUILD_META_ORG_REPO`、`BUILD_META_BRANCH=master`、`QB_SCRIPTS_BRANCH=master`；日志 `buildconf=./build.conf`、`PROJECT_CONFIG` | 尚未发现此 Tizen RBS 表单可写的 build.conf URL/commit/hash 字段；不能宣称改 meta 分支即可覆盖 build.conf |
| 每包 Base CL、shelve、P4 build.conf | VD 变量 `PACKAGE_LIST`、`SHELVE_LIST`、`BASE_REPOS`、`BUILD_CONF`、`PRODUCT_REPOS` | 属 Cosmos 已有资料；提交 UI 的准确控件名、联动、默认值仍待该工作线确认，见 Q7 |

证据：`E15:877` 起完整表单表、`D:1109`、`D:1110`、`T/build-1213815-variables.json`、`T/build-1213816.log:327`、`C:353`、`C:492`。历史 HTML name 例如 Build Package List 是 `editor:content:basicProperties:8:property:editor:editor:wrapper:input`，但编号会随配置变化，Wicket 回调/action 又含会话页号；**这些是取证定位信息，不是稳定提交 API**（`D:54`）。

## Q3：完成后到哪里读取实际版本？近期成功实例

**结论：已证实可以交叉读取全量源码 revision、Profile/base 快照和仓库发布的 build.conf 内容摘要；最终 worker 实际消费的 build.conf 字节摘要仍未知。**

实例是已有构建 **1213815 → 子构建 1213816**，不是本次触发。父页面显示开始于 **2026-10-30 06:13:18**、`Successful`、耗时 23 分 59 秒；Child Build 的 `standard-armv7l:aarch64:x86_64` 为 `SUCCESSFUL`。证据 `T/build-1213815-overview.txt:107` 起、`T/build-1213816-overview.txt`。

| 需要读回的信息 | 读取位置与样本结果 | 本地证据 |
|---|---|---|
| 构建身份、父子关系、状态、产物入口 | `https://quickbuild.tizen.org/build/1213815/overview`；Child Build 链到 1213816；子 `TRIGGER_ID=1213815` | `T/build-1213815-overview.txt`、`T/build-1213816-variables.json` |
| 全量 repo→commit | `/build/1213815/variables` 与 `/build/1213816/variables` 的 `BUILD_PKG_LIST`；各 251 条且完全一致 | 两份 `T/build-*-variables.json`；`T/comparison.json` |
| 归档 manifest | overview 的 `Manifest_URL` → `builddata/manifest/` → standard XML；输出 manifest 251 条，与父/子清单完全一致 | `T/rbs-20261030-manifest-index.html`、`T/manifest-20261030.xml`、`T/comparison.json` |
| 具体包例子 | 输出 manifest `platform/upstream/libtirpc@7623cb042a74f4dfb2d3fe0dc4db0cf3863dd3f0`；新增 `platform/upstream/vtable-dumper@6af6a7d8a664ceaaa38d580ef9c5e025b764c635` | `T/manifest-20261030.xml:102`、`:233` |
| Profile 来源 | 父 overview/变量：Snapshot Number `20261028.234757`；对比原 manifest，250 个已有项目全部 revision 不变，仅增 vtable-dumper | `T/manifest-input-20261028.xml`、`T/comparison.json` |
| 构建根 base | 父 overview 为 `/reference`；子变量是 Ref. Snapshot / `20261013.024319`；子日志打印解析后的 base packages/debug 仓库为该 Oct-13 快照，Profile Oct-28 仓库只是配置中被注释的备选 repos 项 | `T/build-1213816.log:309` 至 `:345`；子变量 JSON |
| 日志版本字典 | 父 `/build/1213815/log` 的完整日志中 `build_pkg_list_dic`；同时有源码获取命令记录，可按包继续核对 | `T/build-1213815.log:1744`、`:2288`；解析方法 `L/tizen-ci-triage/scripts/ci_triage/quickbuild_log.py:19` |

manifest 与变量相符证明**记录的源码输入一致**，不能单凭它证明每个包重新编译且没有使用缓存。全量构建失败也不等于目标包失败（`D:46`）；包级结果还要读报告/包日志。

build.conf 的读取要分三层：

1. **构建日志中的配置**：子日志记录 `buildconf=./build.conf`（`:327`）和 `get_build_conf_text` 的 repo URL（`:344`）；父日志打印 `PROJECT_CONFIG`（`T/build-1213815.log:1039` 起）。没有找到最终 `./build.conf` 的内容 hash 或对应 meta Git commit，不能将这一片段当成完整文件版本证明。
2. **基础仓库发布的配置**：Oct-13 base 的 `repos/standard/packages/repodata/repomd.xml` 中 `<data type="build">` 指向 `*-build.conf.gz`。压缩文件 SHA256 为 `f96236003d723509db9150df3987263ea7836b89fd1a3a1d2cde3e9f6cc52544`；解压内容 SHA256 为 `e5187fd758a663eec273a434090aaab9f8e32f80a036e3bca2cf0352dd286945`（11,171 字节）。已下载并与 checksum/open-checksum 核验。
3. **输出仓库发布的配置**：Oct-30 输出 RBS 仓库同一 repodata 位置的压缩 SHA256 为 `02fca0396be6ab06a0202fb8fe7d62f32b65847defc350f85c65c4e945f8a086`；解压 SHA256 为 `8f201a0d58eb634e60a1f213f47fc09dfa953d9869cdc5724f326a76203587bf`（11,448 字节）。它与 base 配置不同，不能直接称为构建根实际消费的文件。

第 2、3 层证据：`T/base-20261013-repomd.xml:55`、`T/output-20261030-repomd.xml:55`、对应 `*-build.conf.gz`、`T/comparison.json`。离线复核脚本 `T/compare-evidence.py` 只读这些文件，没有连接服务或运行构建。

因此后端可以记录“发布的配置内容摘要”，但若要保证“本次实际使用的 build.conf”，还需要服务端给出生成后文件及 hash 的归档证据；本次未取得。

## Q4：两次输入能否保证只差 patch？

**结论：已证实，重复填写相同表单不足以提供此保证；完整可复现输入方案尚未证实。**

| 潜在变化 | 证据与标注 |
|---|---|
| reference 是滚动入口 | `D:78`、`:1127` 记载由 Sept-24 滚动到 Oct-13；已证实。锁住表单值只是旧客户端策略，不是服务端冻结功能 |
| Profile 与 base 是两条输入链 | 本次父 Profile Oct-28，子构建根 Oct-13；`T/build-1213816.log:311`。已证实；只固定 Profile 不足以证明 base 固定 |
| 构建脚本/元配置使用可变分支 | 父日志 `:22`、`:40` 与子日志 `:108`、`:184` 等多次克隆 `master`；变量也为 master。分支可变、重复读取可能漂移是推断，未证明此样本实际发生漂移 |
| 全量包清单与省略字段 | 默认 reference、项目分支、ADD/MODIFY/RM、架构/镜像/Full/Partial/FAIL_FAST 都须比对；已确认存在这些输入（Q1、Q2），省略时会否随配置改变是风险推断 |
| 缓存、依赖二进制、构建工具及 worker 环境 | 样本有 exported-source cache，日志 `T/build-1213815.log:2280` 起；仅相同源码 revision 不证明依赖、缓存状态及工具完全相同。环境完全等价未知 |
| build.conf 生成链 | 实际文件 hash 未归档确认，输出仓库与 base 配置 hash 不同；Q3。不能把固定 manifest 推升成固定编译配置 |
| VD shelve 可原号更新 | `C:530`、`:771` 记录 shelveUpdate 与提交后取代码前改动的风险；相同 SCL 不等于相同内容。该结论属于 VD，不能套给 Tizen Git commit |

**设计推断：** CodingSystem 应分别保存请求原值与实际读回值：全量包清单、Profile URL、解析后的 base/product 仓库、build.conf 内容摘要/生成依据、脚本与工具链版本、架构及所有影响构建的选项；再比较两次证据，列出明确的 patch 差异。无法固定或读回的项应保留“不保证等价”，不能自动给出“只有 patch 不同”。这是设计建议，不是已存在的 QuickBuild API。

## Q5：镜像、日志在哪里下载，如何命名，保留多久？

**结论：下载入口、样例命名和官网公布的保留政策已证实；各项目的实际清理时点与例外未知。**

| 内容 | 位置 / 命名 | 证据 |
|---|---|---|
| 本次成功构建产物 | overview `Download_URL` 是 `http://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261030.061318`；原 RBS 目录也可读：将 `/snapshots/` 换为 `/RBS/` | `T/build-1213815-overview.txt:102`、`T/rbs-20261030-index.html` |
| 逐包日志 | 产物根下 `builddata/buildlogs/standard/<arch>/succeeded/<包名>.buildlog.txt`；本次 aarch64 有 `libtirpc.buildlog.txt`、`vtable-dumper.buildlog.txt`。历史 Unified 失败分支为 `failed/` | `T/rbs-20261030-aarch64-succeeded.html`；`L/tizen-ci-shared/scripts/tizen_ci_shared/quickbuild_http.py:150` |
| QuickBuild 完整执行日志 | `/build/<id>/log` 页面 **Save** 下载链接。链接是 Wicket 动态地址，不能硬编码当前页号；本地归档命名 `build-1213815.log`、`build-1213816.log` 是调查方命名 | 两份本地 `.log`；上述源码 `:106` 起；本地浏览器审计记录 |
| 报告到包日志 | 子构建 → HTML REPORT → Succeeded / Failed；SBS 历史 iframe 路径 `/download/1069540/html/HTML REPORT/index.html` | `T/quickbuild-user-guide.txt:58`；`E15:725` |
| 镜像 | 依工程而定：本次 Base 样本 `TARGET_IMAGE` 为空，目录没有 images，日志也没有镜像配置。已有 Unified reference 目录则有 `images/standard/tizen-headed-aarch64/`，镜像例 `tizen-unified-toolchain_20261016.052151_tizen-headed-aarch64.tar.gz`，同目录有 `.packages`、`.xml`、`.log`、`manifest.json`、`SHA256SUMS` 等 | `T/rbs-20261030-index.html`、`T/build-1213815.log:2658`；`T/unified-image-aarch64.html`。仅读取目录，未下载大镜像 |

官网 [Quickbuild User Guide](https://quickbuild.tizen.org/guide/index.html) 的政策表（本地证据 `T/quickbuild-user-guide.txt:82` 起）：

| 保存对象 | 公布天数 |
|---|---:|
| QuickBuild Build 记录 | 30 |
| QuickBuild Artifact | 10 |
| 下载站 SBS | 5 |
| 下载站 RBS | 7 |
| 下载站 Snapshots | 10 |
| 下载站 Release Daily | 30 |
| 下载站 Release Weekly / Milestone | 90 |

这些是**站点文档政策**，没有后台配置核验。逐包日志位于下载产物树，可推断受相应产物清理影响；完整日志是否存在独立保留例外、reference/推荐构建是否豁免、删除任务何时执行，均未知。旧 Oct-19 RBS 目录此次已 404（`T/rbs-20261019-404.png`），不能仅凭一次 404 反推固定保留天数。后端需要及时保存证据，不应把远端链接当永久归档。

## Q6：状态、取消和可检索的自定义标记

**结论：已证实有运行、成功、失败、取消、超时及请求标记字段；取消能力只确认入口与历史终态，未执行。**

- **状态（已证实）：** 既有配置页有 `running`、`successful`、`failed`、`cancelled`、`timeout` 的状态 class；例如 1200950 cancelled、1198829 timeout。请求表则显示 `RUNNING_BUILD`。证据 `E20/evidence/C6b/configuration-1917.md:30` 起；此次 `T/configuration-1917.txt:85` 起。queued/waiting 的完整枚举与各状态转换规则未知，不能用客户端自定义状态机冒充服务器枚举。
- **粒度（已证实）：** 父 trigger、子 build、包级编译结果是不同层次。SBS 的接受/发布流程又是另一状态维度；不能要求 RBS `SR_STATUS=ACCEPTED` 才认定编译通过。证据 `D:38`、`:40`、`:46`，以及 Q3 的父/子/manifest 对照。
- **取消（部分已证实）：** 当前页面显示 `cancel selected`、`cancel All`，运行构建行有 `Stop`；历史也存在 cancelled 终态。未点击，当前用户权限、停止是否联动子任务、何时释放资源未知。证据 `T/configuration-1917.txt:85`、`:124`；`E20/evidence/C6b/configuration-1917.md:43`。
- **自定义标记（已证实）：** 表单 **BUILD NOTES** → `BUILD_NOTES`。既有成功构建 1201886 回显 `clang-fix-campaign request=9fe02dc3927c4b7fa55a3dffce699d03`，与提交标记逐字一致。证据 `E15:891`、`D:1126`。此次没有填写新标记。另有 UI 标签/描述是否可在提交时写入，未确认。
- **精确找回（推断 / 已有客户端设计）：** 从配置 Recent Builds 的候选 ID 读取父构建 `BUILD_NOTES`，精确匹配唯一 request UUID，同时核对工程、时间、包清单与父子关系；立即保存 build ID。Recent Builds 只显示最近 10 个，不能保证很久后仍能从该页找回，也没有证据表明列表支持服务端按备注全文搜索。依据 `D:48`、`:1129`、`:1126`。推广标签、版本时间戳或提交人都不能替代独立 request ID。

## Q7：Cosmos（VD）有何不同？仅引用已有资料

**结论：已证实（既有侦察记录）VD 使用 P4 Base CL / shelve 和独立 BUILD_CONF 输入；实际 shelve 同步/合并细节及若干提交能力仍未知。** 全部来源为远端 `vd-cosmos-loganalyzer@b6b7c09` 的 `C`，没有访问 Cosmos。

| 对应问题 | VD Cosmos 的已有事实 / 差异 | 标注与证据 |
|---|---|---|
| Q1 版本模型 | VD 请求包含每包 `路径/...@CL` 的 base 清单（包括 shelve 包）和单独 shelve 清单；与公开 Tizen 的 Git repo@commit 不同。普通报告行显示 CL，shelve 行显示 shelve 分支路径与 SCL，**不会另给 base 行** | 已证实（既有记录）；`C:175`、`:490`、`:1442`、`:1448` |
| Q1 base 与 patch 应用 | VD 本地模拟先按请求清单同步再 unshelve；但这不是 Cosmos 执行端同样同步/resolve 的证明。shelve 包未改文件是否确按请求 base、跨分支如何应用、旧基础文件如何合并仍待确认 | 本地做法已记录；服务端细节未知；`C:1448`、`:1100`、`:1102`。工具三方合并属于设计裁定，不能写成服务端已证实事实 |
| Q2 显式输入 | 业务输入有 Clang build.conf 的 P4 版本、LLVM base 快照、Base CL 和 shelve 清单。变量页已确认 `PACKAGE_LIST`、`SHELVE_LIST`、`BASE_REPOS`、`BUILD_CONF`、`PRODUCT_REPOS`。提交表单的准确 HTML 控件名、默认/留空行为及回调仍未定 | 输入及读回变量已证实，具体提交映射未知；`C:175`、`:492`、`:1449`；未决 `C:353`、`:1084` |
| Q3 结果读回 | 管理实例 `/build/<id>/variables` 能读上述五变量；静态报告头有 BASE SNAPSHOT / PRODUCT SNAPSHOT / BUILD CONF（P4 depot 路径@CL）。构建 19091860 的 PACKAGE_LIST 2245 行、SHELVE_LIST 545 行；非 shelve 1699 行与报告完全一致，545 个 shelve 报告行均能找到请求 base，清单比报告多 1 包 | 已证实（既有 10-30 只读侦察）；`C:339`、`:492`、`:1449`、`:1450`。请求 base 可找回仍不等于 shelve 实际同步 CL 已证明 |
| Q4 两轮可比性 | 同一个 shelve CL 可重新 shelve，须检查内容摘要和 `shelveUpdate`；只记 SCL 不足以还原历史输入。现有 `fix5h_base_urls.txt` 已有 51 个包 CL 更新，不能拿当前文件充当构建 19091860 的历史输入 | 已证实（已有侦察及工作线记录）；`C:530`、`:1450`。提交后至服务端取代码前的变化仍有残余风险，`C:771` |
| Q5 报告/日志/镜像 | 报告 `<报告根>/b<构建号末三位>/<构建号>/html/Build_Report_<架构>/index.html`；包日志在其下 `logs/fail/<包名-版本-发布号>/log.txt` 或 `logs/success/.../log.txt`；同级 Profiling_Report。base/product 有 builddata、repodata；不同架构报告可相差约两小时发布 | 已证实；`C:339`、`:348`、`:1443`。镜像实际下载文件命名、镜像/日志保留天数未知；不能套 Tizen 下载站政策 |
| Q6 状态/取消/标记 | 构建 19091860 的头部有唯一 `title="Build is …"`，值 failed；构建号须从头部自身链接确认，不能用下游推广号。提交实例走公司 SSO，读取实例访客可读 | 已证实；`C:339`、`:1440`。运行/排队实词、取消权限/语义、可写请求标记和提交/管理实例构建号映射仍未知：`C:353`、`:1084`、`:1086` |
| Q8 并发/配额 | HLD 的 flock、轮次事务锁、上一轮结束闸门是客户端协调策略，不是 Cosmos 平台配额 | 平台上限未知；`C:898` 起、`:725`。没有据此声称只能跑一个构建 |

补充解释：Cosmos 报告头的 BUILD CONF 是可指向 P4 版本的输入标识，公开 Tizen 样本目前只取得发布仓库 build.conf hash，二者的证据能力不同。Cosmos 也不能仅凭报告里的 `(shelve)` 行还原 base，必须结合变量页清单；对应关系应保留原始 depot 分支，不能把不同 depot 文件的 `#rev` 当同一序列（`C:502` 起）。

## Q8：并发与配额

**结论：并发上限与配额未知；已证实当前 Base RBS 配置存在至少三个同时处于运行态的父请求。**

2026-11-02 的配置 1917 只读快照显示三行 `RUNNING_BUILD`，对应 1214877、1215122、1215143；Recent Builds 各有 Stop/进度。证据 `T/configuration-1917.txt:85` 至 `:146`。这证明不是“该配置永远只能有一个运行态请求”，**不能证明三个子编译任务当时都在占用 worker，也不能推出上限就是三**。

现有资料没有给出每用户、每项目、全局并发、队列长度、优先级配额、CPU/内存预算或提交频率的数字上限。官网仅列角色权限：Developer 可查看、Maintainer 可 SBS、Manager 可 RBS/Release（`T/quickbuild-user-guide.txt:64` 起）。这些是权限，不是配额。Recent Builds 的 10 行是展示窗口；日志中的 VM CPU/内存是单次资源参数；旧工具的超时/重试预算也不是服务端并发限额。Cosmos 的并发上限同样未知（Q7）。

因此后端设计中可配置客户端并发限制，但应明确它是本系统限流策略；实际平台容量、拒绝/排队规则以及取消后的配额释放时点仍需要管理员资料或另行授权的验证。本次没有通过真实提交探测这些边界。
