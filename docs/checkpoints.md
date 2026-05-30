# Checkpoints 登记表

| Tag | Commit Hash | 覆盖范围 | 回退指令 | 回退后状态描述 |
|---|---|---|---|---|
| `checkpoint/phase_1a_sprint_0_spike_complete` | `a4ff9fc401ac4856a3bf0af787c785b6d928f0d5` | Phase 1A Sprint 0 spike closeout: S0-01 prerequisite + S0-02~S0-09 eight core gates confirmed PASS; includes Sprint 0 dev memory; no product code; S0-10 not started. | `git reset --hard checkpoint/phase_1a_sprint_0_spike_complete` | 回到 Sprint 0 spike 收官报告状态，可在用户确认后按 Sprint 1+ prompt 进入 Sprint 1；`check_gate.sh` 尚未创建。 |

## 说明

每个 Sprint 完成、Review 闭环后，在此登记 checkpoint：
- Tag 命名：`checkpoint/phase_{N}_{shortdesc}`
- Commit hash：该 tag 指向的 commit
- 覆盖范围：本 checkpoint 包含哪些功能
- 回退指令：`git reset --hard checkpoint/phase_{N}_{shortdesc}`
- 回退后状态描述：一句话说明回到这里时项目处于什么状态
