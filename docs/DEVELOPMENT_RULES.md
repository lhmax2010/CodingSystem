# Coding System 开发规约（R1–R14）

**适用对象**：Codex（AI 开发主体）
**重要调整**：本项目 **不走 GitHub PR 工作流**，直接 git push 到 main 分支（详见下方"PR 工作流调整"）。

---

## 0. 本项目的工作流调整（覆盖原 R9/R10/R14 的 PR 约束）

为方便 review，本项目**不使用 GitHub PR**，改用以下流程：

| 原规约（PR 工作流） | 本项目调整（直接 push） |
|---|---|
| 每阶段创建 `phase/{N}-...` 分支 | 直接在 `codex/sprint-N-main` 分支开发，完成后 merge 到 main 并 `git push origin main` |
| 创建 GitHub PR，PR 标题 `[Phase N] ...` | **不创建 PR**。用 review_packet 文件替代 PR 描述 |
| R10 PR 能力预检 | 改为 **Git push 能力预检**：验证是 git 仓库 / 有 remote / 能 push 到 main |
| Review AI 反馈贴在 PR | Review AI 反馈写入 `docs/review/phase_{N}_review_result.md` |
| R3 交付物含"GitHub PR 链接" | 改为"commit hash + branch + push 记录" |

**其余 R1-R14 规约全部保留。**

---

## R1. 设计文档不可变性 + 设计反向 Review

- 开发过程中**严禁自作主张修改设计文档**（`docs/baseline/` 全部 Frozen）。
- **Sprint 0 / Phase 1 启动前的强制设计 Review**：
  - 写任何代码前，先通读 `docs/baseline/` 全部 + `docs/prompts/` + `docs/adr/`。
  - 输出 `docs/review/design_review_sprint_0.md`，逐项审查：
    - 设计能否满足需求（覆盖度）
    - 模块划分 / 数据流 / 接口契约是否有不合理或错误
    - 是否有**更好的方案**
    - Sprint 拆分是否合理，依赖关系是否成立
    - 非功能性约束是否可落地
  - 发现问题输出 `[DESIGN_ISSUE]` / `[DESIGN_SUGGESTION]` 列表 + 建议方案，**暂停等待 user 决策**。
- **任何阶段开发中**发现设计缺陷/矛盾/更好方案：
  - **暂停**，输出 `[DESIGN_ISSUE]` + 问题描述 + ≥1 个建议方案。
  - 创建 `docs/design_changes/change_{N}.md`（背景/问题/影响范围/备选方案/风险/是否影响 checkpoint/是否需返工/待确认问题）。
  - 等 user 确认。**不得自作主张修改设计**。
- 确认修改后，**由 user 更新 baseline 文档并升版本号**；AI 不得直接改。

## R2. 决策边界（人工介入门槛）

**必须按规划继续，不要问**：
- "下一步做什么"——v2.1.2 已写好 Sprint 顺序，按序推进
- "要不要开始 Sprint N"——上一阶段 DoD 满足就开始
- 变量命名/函数位置/测试补充/私有函数拆分/内部数据结构——自行决策
- 只有一个合理方案时，直接做，不要"礼貌性确认"

**必须暂停询问**（触发任一立刻停）：
- 出现 ≥2 个实现方案：列出取舍让 user 选
- 引入/升级/降级/替换任何第三方依赖
- 修改公共 API 或跨阶段接口契约
- 数据模型 / Schema 变更
- 安全模型调整（认证/鉴权/加密/Token/密钥/权限边界）
- 性能预算取舍
- 部署方式 / 运行环境变更
- 兼容性 / 向后兼容
- 回滚策略
- 大范围重构（R11）
- 设计与需求矛盾或设计有缺陷（R1）

## R3. 每阶段交付物（缺一不可）

每个 Sprint 完成时必须输出 5 项：

1. **代码**：实现 + 单元测试 + 必要集成测试
   - 不引入与本阶段无关的 diff（不顺手重命名/重构/格式化）
   - 不升级无关依赖
   - 不引入任何 secret/token/私钥/密码/敏感日志（走环境变量或 Secret Manager）
2. **UT 报告**：
   - 通过/失败数
   - **行覆盖率 ≥ 80%，分支覆盖率 ≥ 70%**（关键模块 ≥ 90%）
   - 覆盖率报告路径
   - Coverage 例外需在 Review Prompt 说明（generated code / 纯类型 / framework glue / 平台启动代码 / 难运行的外部集成；**核心业务逻辑不得豁免**）
3. **dev_memory.md**（`docs/dev_memory/phase_{N}_memory.md`）：
   - 实现思路与关键决策（"为什么"而非"做了什么"）
   - 走过的弯路与放弃的方案
   - 与设计文档的偏差（如有，须经 R1 确认）
   - 遗留 TODO 与已知限制
   - 写作要求：陌生 AI/工程师 10 分钟内能恢复上下文
4. **checkpoint**：
   - Git tag：`checkpoint/phase_{N}_{shortdesc}`，指向通过 UT 的 commit
   - 登记到 `docs/checkpoints.md`：tag、commit hash、覆盖范围、回退指令、**回退后状态描述**（一句话）
5. **Review Prompt**（`docs/review/phase_{N}_review_prompt.md`）：
   - 发给 Review AI 做代码 + 设计审查
   - 必须含：
     - 本阶段变更文件清单
     - 设计文档对应章节链接/编号
     - UT 结果与覆盖率（含 R13 实际执行命令与输出摘要）
     - **commit hash + branch + push 记录**（替代原 PR 链接）
     - 重点审查项（性能热点/安全点/并发点）
     - 已知未覆盖场景
     - Coverage 例外说明（如有）
   - Review AI 职责（写入 Review Prompt）：
     1. 审查代码质量、UT 充分性、是否符合设计
     2. 同时审查设计本身暴露的问题或更好方案
     3. 每条反馈带严重等级：`[BLOCKER]` / `[MAJOR]` / `[MINOR]` / `[NIT]`
     4. 反馈类型标签：`[CODE_ISSUE]` / `[DESIGN_SUGGESTION]` / `[ALTERNATIVE]`
     5. 不得自行修改代码或设计，只输出建议
   - 反馈保存到 `docs/review/phase_{N}_review_result.md`

## R4. Subagent 隔离协议

与当前阶段无关的新需求/想法：
- 不要 compact 进主上下文
- 不要中断当前阶段
- 启动 subagent 在独立分支处理，结果写入 `docs/spinoffs/{topic}.md`
- 主 agent 继续按设计推进

## R5. 检查点回滚

user 说"回到 checkpoint X"：
- `git reset --hard checkpoint/phase_X_*`
- 读该阶段 dev_memory.md 恢复上下文
- 确认无误后继续

## R6. 上下文加载顺序（每次会话开始）

1. 读 `docs/README.md`（文档索引）
2. 读 `docs/baseline/`（设计基线全文）
3. 读 `docs/adr/`（架构决策）
4. 读 `docs/design_changes/`（已批准的设计变更）
5. 读 `docs/dev_memory/` 下所有已完成阶段 memory
6. 读 `docs/checkpoints.md` 了解当前阶段
7. 读 `docs/review/*_review_result.md` 了解上一阶段 Review 闭环
8. 读 `docs/spinoffs/` 了解被隔离的讨论
9. 然后才开始本次任务

## R7. 非功能性约束

- **日志**：关键路径结构化日志（trace_id/level/业务字段）。严禁打印密钥/Token/PII
- **错误处理**：所有外部调用有超时 + 重试 + 降级
- **安全**：密钥/Token 走环境变量或 Secret Manager，严禁硬编码；用户输入必须校验
- **性能**：标注关键路径性能预算（如 P95 < 200ms），UT 加基准或集成测试校验
- **可观测性**：关键业务指标埋点（成功率/延迟/错误码分布）

## R8. 依赖管理

- 锁定版本（package-lock.json / poetry.lock / go.sum），不随手升级
- 引入/升级/降级/替换依赖必须经 R2 询问

## R9. Git 规范（已调整为直接 push）

- 分支：`codex/sprint-{N}-main`（与 MAIN_PROMPT v2.2 一致；风险隔离任务才用 `codex/sprint-{N}-task-{X}`）
- Commit message：`[Sprint N] <type>: <subject>`（conventional commits）
- **不创建 PR**。每个 Sprint 完成、review 通过后，merge 到 main 并 `git push origin main`
- review_packet 文件（`docs/review/phase_{N}_review_prompt.md`）替代 PR 描述

## R10. Git Push 能力预检（已调整，替代原 PR 预检）

Sprint 0 编码前，检查：
- 是否是 Git 仓库
- 是否有 remote
- 是否能 commit + push 到 main
- 是否能按 `codex/sprint-{N}-main` 创建分支
- 是否能打 tag（checkpoint 用）

如发现无法 push / remote 不存在 / 权限不足，输出 `[GIT_WORKFLOW_ISSUE]` + 问题描述 + 当前仓库状态 + 对 Review 流程的影响 + 可选方案，**暂停等 user 决定**。

## R11. 大范围重构控制

- 每个 Sprint 只改与当前阶段目标**直接相关**的文件
- 禁止顺手重构/升级/重命名/调风格/清理无关代码
- 如必须大范围重构（≥3 模块或公共接口变更），**暂停**输出 `[REFACTOR_PROPOSAL]`（为什么/不重构的风险/范围/涉及文件/对接口测试数据模型 checkpoint 的影响/替代方案/推荐方案），等 user 确认
- 与当前 Sprint 无关的重构，拆成独立 Sprint 或写入 `docs/spinoffs/`

## R12. 现有项目优先原则

开发前扫描现有仓库：README/docs、build 脚本与包管理文件、测试框架与配置、lint/format 配置、CI 配置、现有模块边界与目录约定、现有日志/配置注入/错误处理方式、现有代码风格。

新增代码**优先复用**现有结构、工具链、测试框架、日志框架、配置方式。

**不得凭空创建**与现有项目冲突的新目录/框架/构建方式。

如 baseline 文档的目录结构/技术方案/测试方案与现有项目明显冲突，输出 `[DESIGN_ISSUE]` 并按 R1 暂停。

## R13. 测试真实性与命令记录

每个 Sprint 完成时记录**实际执行过**的验证命令（不是"声称"）：
- build / lint / format check / type check / UT / coverage / integration test 命令

**不得声称"测试通过"而不提供输出摘要**。每条命令附：实际命令字符串 + 输出摘要（关键行）+ 通过/失败状态。

无法运行的测试必须说明：未运行原因 / 缺失环境 / 替代验证 / 需 user 本地执行的命令。

测试结果同时写入 `docs/dev_memory/phase_{N}_memory.md` 和 `docs/review/phase_{N}_review_prompt.md`。

## R14. Review 闭环规则（已调整：无 PR）

Review AI 反馈必须形成闭环：
- Coding AI 处理规则：
  - `[BLOCKER]` 必须修复，修复后才能 merge 到 main
  - `[MAJOR]` 原则上必须修复；不修复需 user 在 `phase_{N}_review_result.md` 显式确认放行
  - `[MINOR]` 可记录到 dev_memory.md 的"遗留 TODO"
  - `[NIT]` 不阻塞，可选采纳
- 修复后更新：代码 + 测试 + dev_memory.md（修复思路）+ phase_{N}_review_result.md（每条反馈处理结果：已修复/已确认放行/转 TODO/拒绝采纳）
- `[DESIGN_SUGGESTION]` / `[ALTERNATIVE]` 必须走 R1 设计变更提案流程，不得直接改设计或自行返工
- **闭环通过后才 merge 到 main 并 push**

---

## 与本项目 baseline 的映射

本 R1-R14 规约与 baseline 文档的对应关系：

| R 规约 | baseline 中的对应 |
|---|---|
| R1 设计不可变 | MAIN_PROMPT v2.2 §1.3 文档冲突处理 |
| R3 交付物 | MAIN_PROMPT v2.2 §3.3 review_packet + §3.4 dev_memory |
| R3 覆盖率 | 开发计划 v2.1.2 check_gate.sh gate 2 |
| R7 非功能性 | Team Contract v0.7.2 §5.6 Raw Log / Secret Redaction |
| R13 测试命令 | 开发计划 v2.1.2 check_gate.sh（8 blocking + 1 advisory） |
| R14 Review 闭环 | SPRINT_1_PLUS v1.2 §3.3 review_packet 流程 |

如有冲突，以本 DEVELOPMENT_RULES.md 的 git push 调整为准（针对 PR 部分），其余以 baseline 为准。

---

**开发规约结束。**
