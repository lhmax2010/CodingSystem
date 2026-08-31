# Decision Log

1. 仓库结构依据 `docs/00_Framework_HLD_v0.1.md` §10 建立。
2. 旧版 `main` 全量保留于 `backup/pre-restart-20260831`。
3. `main` 保留连续历史，未重开 orphan；backup 分支使旧对象必然保留，重开历史无收益且需 force push。
