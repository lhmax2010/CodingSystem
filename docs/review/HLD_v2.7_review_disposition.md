# HLD v2.7 第七轮定向复审处置表（→ v2.8）

裁决输入：Kimi **GO**（0 / 0 / 0 / 0）；Codex **GO**（0 / 0 / 0 / 1 NIT）；Claude Code **GO**（0 BLOCKER / 0 MAJOR / 1 MINOR / 1 NIT）。HLD 部分**三家一致 GO**。合计 3 条意见，**全部采纳**，均为边界补全，不改架构。负责人七项裁决三家均判成立。

| # | 问题 | 来源 | 处置 |
|---|------|------|------|
| P1 | 完成事务复核只写了"成功"与"父版本 CAS 失败"两种结局；CAS 通过、但计划状态（收益判定写回不推进 series）或准入（不推进 series 的环消耗次数）已变化时，复核结论与预校验不同，出口未定义——若按复核结论改记 purpose，会让按撤销提交的段以修复名义回退已接受的优化 | CC H27-01（MINOR） | 采用。与父版本 CAS 失败同一出口：候选作废、计划与 series 不变、sys.error(candidate_recheck_failed) 按节点重试、重试时重新预校验；不得改记 purpose |
| P2 | 改交撤销规则"以其他 status 结束即违规"没有排除镜像节点合法的 base_mismatch / backend_source_input_unsupported 出口；被预校验拒绝的提交若登记为 candidate，会挡住随后的改交 | CC H27-02（NIT） | 采用。写明例外；被拒提交不登记 candidate，改交用新 request_id |
| P3 | §11.3 旧 terminal 兜底用例的前置（image_failed_exhausted 路由到 terminal）已被规则③在加载期拒绝，与新用例期望相反 | Codex H27-01（NIT） | 采用。改为绕过加载器直接构造状态的单元测试，合法图的可达性由 v2.7 用例组检验 |

## 负责人新增前提

| # | 前提 | 处置 |
|---|------|------|
| P4 | 整个产品不得引入 PHP（项目负责人 2026-11-05） | 新增 D23：覆盖全部交付与部署内容（框架、各 Agent、Approval 服务、Release broker 与官方 adapter、Build Gateway 与登录助手、Web 视图、deploy 资产与镜像、测试夹具）及其运行时依赖闭包；业务接入的 Agent 插件与受限发布 adapter、Benchmark 宿主侧解析规则在注册时声明运行时，PHP 一律拒绝。边界：对接的外部系统（Quickbuild、gerrit、github、Cosmos）实现语言不在范围内；只在测试板上执行的业务用例脚本不属于本产品交付物。§11.1 技术栈、§11.2 门禁（依赖闭包与交付物扫描、注册时运行时检查）、§9、附录 B 同步。现文中原本没有任何 PHP 组件，本条为显式约束与检查 |

## 结论

HLD 已连续两轮三家 GO，本轮只有 MINOR / NIT。**HLD 定稿为 v2.8**，可作为与总部对齐和开发的基线；后续只随 01 同步做必要的一致性修订。
