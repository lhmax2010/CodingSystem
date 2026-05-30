# Checkpoints 登记表

| Tag | Commit Hash | 覆盖范围 | 回退指令 | 回退后状态描述 |
|---|---|---|---|---|
| `checkpoint/phase_1a_sprint_0_spike_complete` | `a4ff9fc401ac4856a3bf0af787c785b6d928f0d5` | Sprint 0 Spike Gate 全部 9 任务完成（S0-01 + 8 个核心 gate S0-02~S0-09，全部标记 PASS） | `git reset --hard checkpoint/phase_1a_sprint_0_spike_complete` | Sprint 0 pre-repair 证据管线机制验证完成（注：经外部 review 后定性已降级，详见 change_3） |
| `checkpoint/phase_1a_sprint_0_remediated` | `0f419328b1e1ac1fad2eb1f6b92d5dfe5a9df4e0` | change_3 第一批完成：S0-01~S0-04 frozen artifacts 恢复；9 gate artifact_manifest 加 SHA256；Sprint 0 定性降级；S0-08 改为 pre-LLM pipeline dry run；token/cascade 口径修正。未包含 S0-A/S0-C。 | `git reset --hard checkpoint/phase_1a_sprint_0_remediated` | 回到 Sprint 0 审计修复 + 定性修正完成状态；下一步仍需 PM 确认后启动 S0-A/S0-C，不能直接进 Sprint 1。 |

## 注意：Sprint 0 定性已修正

按 change_3（ChatGPT + Kimi 外部 review）的修正，此 checkpoint 实际验证范围是：

> **CNEI pre-repair 证据管线机制在单包受控 spike 条件下可行**

**未验证**（进 Sprint 1 前必须补，见 S0-A / S0-C 任务定义）：
- LLM 真实修复准确率
- 修复闭环（worktree / patch / bounded repair）
- 跨包能力
- 真实 patch 成功率

进 Sprint 1 前的强制前置见开发计划 v2.1.5。

## 说明

每个 Sprint 完成、Review 闭环后，在此登记 checkpoint：
- Tag 命名：`checkpoint/phase_{N}_{shortdesc}`
- Commit hash：该 tag 指向的 commit
- 覆盖范围：本 checkpoint 包含哪些功能
- 回退指令：`git reset --hard checkpoint/phase_{N}_{shortdesc}`
- 回退后状态描述：一句话说明回到这里时项目处于什么状态
