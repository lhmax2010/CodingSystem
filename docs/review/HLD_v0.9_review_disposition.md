# HLD v0.9 三方复审处置表（→ v0.10）

裁决输入：Claude Code **GO**（历轮 issue 全清、同意 freeze，2 NIT + 1 CLARIFY）、Kimi NO-GO（1 MAJOR + 1 NIT）、Codex NO-GO（1 BLOCKER + 1 MAJOR）。
关键事实：**簇 AC 的仲裁选择获三方一致接受**（CC/Kimi 均正面表态"仲裁理由成立、方案优于本方"）；两处接口定案（effect_class / post-close correction）三方一致关闭。两家 NO-GO 的实质意见共同指向条件③自身的两个补全面 + 一处 v0.9 措辞矛盾，全部成立采纳。

## 共识簇（条件③补全——同一根因的两个面，互相咬合成完整修法）

| 簇 | 覆盖 | 处置 | 落点 |
|----|------|------|------|
| AD 条件③退役不级联、替代 cohort 无保证 | Kimi M-01(MAJOR，级联面：嵌套子 activation 计时器误杀 + 死 scope 分派无处置)；Codex R9-01(BLOCKER，重建面：分支内回环不重经 fan-out 则兄弟来源永不重派 + 环 activation 父 scope 未定)；CC CL-β(父继承落点提醒，同题) | 采纳（三家意见合并落文） | §4.2.4 条件③重写：退役沿 parent_activation_id **级联全部子孙**并作废各自计时器（Kimi 主修法）；join 消费/分派/timeout CAS 增加**祖先链无 superseded** 校验、死 scope 分派拒绝并审计（Kimi 的"或"项作防御性双保险一并落入）；§4.2.6 条件(iii)**静态收敛**——环边回流必须重经该 join 的共同 fan-out 从而重派全部来源分区，分支内回环拒绝加载（Codex 主修法；旗舰示例复核：ut_fix→compiler→build_passed 重新 fan-out 双分支，通过）；**替代 cohort 继承被退役者 parent_activation_id、环不插入额外嵌套层级**（Codex + CC CL-β 同答）；§11.3 补三组断言/property |

## Codex（R9-01–R9-02）——全采纳

| # | 处置 | 落点 |
|---|------|------|
| R9-01 BLOCKER | 采纳 | 簇 AD（其静态收敛方案 + 父继承规定原文落定） |
| R9-02 | 采纳 | §5.2：v0.9 的"对账清零（三支对账后退役 abandoned）"括注确与三支终态矛盾（succeeded/unknown 被改写会致重复外部效应或绕过 fail-closed）——属 v0.9 修订引入的措辞 bug。改为**逐支定态**（probe 成功→succeeded 复用、未发生/replay_safe→abandoned、不可判定→unknown+sys.error），succeeded/unknown 不得改写为 abandoned，异参新键仅立于允许继续的终态之上；§11.3 补矩阵测试 |

## Kimi（M-01–M-02）——全采纳

| # | 处置 | 落点 |
|---|------|------|
| M-01 MAJOR | 采纳 | 簇 AD（其级联反例与死 scope 分派两形态均落文；取级联为主修法、祖先链 CAS 为双保险——两案并落而非二选一，成本均为句级） |
| M-02 | 采纳 | 条件③措辞改"采用该环边的 task 所属 activation 上下文"（与 CC AA-02 合并） |

## Claude Code（AA-01–AA-02 + CL-β）——GO，全采纳

| # | 处置 | 落点 |
|---|------|------|
| AA-01 | 采纳 | 条件③重写时重复 no-op 句合并（段末统一表述保留） |
| AA-02 | 采纳 | 同 Kimi M-02 |
| CL-β | 已答 | 替代 cohort 父继承已在条件③正文写明（不再仅留 [01]） |

## 汇总
- 全部条目采纳；无方案裁剪。簇 AD 是条件③（上轮新机制）的自身补全，非既关闭问题重开。
- 九轮 BLOCKER 轨迹：13→3→7→5→4→2→1→1→1。三方在簇 AC 仲裁、B3 发布安全、两处接口定案上已全部对齐；CC 已全清并同意 freeze，Kimi/Codex 均明示本轮问题修入即可。
- v0.10 复审重点：(1) 条件③级联 + 祖先链 CAS + 静态收敛三件套是否闭合（含旗舰示例与嵌套图复演）；(2) 跨 attempt 逐支定态与异参新键规则。两点均为三家自给方案的合并落文。
