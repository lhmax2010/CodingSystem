# Checkpoints 登记表

| Tag | Commit Hash | 覆盖范围 | 回退指令 | 回退后状态描述 |
|---|---|---|---|---|
| (待 Sprint 完成后登记) | | | | |

## 说明

每个 Sprint 完成、Review 闭环后，在此登记 checkpoint：
- Tag 命名：`checkpoint/phase_{N}_{shortdesc}`
- Commit hash：该 tag 指向的 commit
- 覆盖范围：本 checkpoint 包含哪些功能
- 回退指令：`git reset --hard checkpoint/phase_{N}_{shortdesc}`
- 回退后状态描述：一句话说明回到这里时项目处于什么状态
