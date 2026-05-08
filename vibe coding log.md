# dizical vibe coding log

## 2026-05-08 (Fri) — Kid Interface Session

### 工作内容
- **practice_query TUI bugs 修复**：
  - `curses.nodelay` 模式导致 CPU 高占用
  - `_fuzzy_match` 返回 None 未处理
  - h 键导航到 homework view
- **Kid iPad 界面 review**：测试 5 个页面（prepare/practice/achievements/report/praise）
- **PRD 编写**：`PRD-kid-interface-v0.1.md` 已保存到 Obsidian
- **问题追踪**：发现 9 个 issues，P0 bugs 在 `feat/kid-ui-refresh` 修复中

### Kid Interface 发现的问题（9个）
| # | 页面 | 问题 |
|---|------|------|
| 1 | practice | 打卡后无进度记录显示 |
| 2 | practice | 重复打卡不拦截 |
| 3 | practice | 打卡成功提示不够明确 |
| 4 | achievements | 无打卡记录时显示空白 |
| 5 | achievements | 进度条动画缺失 |
| 6 | prepare | 准备页内容静态 |
| 7 | prepare | 每日一练卡片缺失 |
| 8 | praise | 鼓励页静态 |
| 9 | praise | 鼓励语无个性化 |

### 文档
- PRD: `tqob/05 Coding/project-dizical/PRD-kid-interface-v0.1.md`

### 分支
- worktree: `hermes/hermes-3bb46bdd`
- 功能分支: `feat/kid-ui-refresh`

---

## 2026-04-30 (Thu)

### 每周老师要求导入
- 命令: `dizical practice import-assignments data/imports/import-assignments.csv`
- 结果: ✅ 17 周全部导入成功
- CSV 格式: `WeekStart,Item,Requirement,Notes`（日期格式 `YYYY/M/D`）

---

## 2026-04-28 (Mon)

### 状态检查
- 分支: `hermes/hermes-f001fa86` (worktree 模式)
- main 与 worktree 分支完全同步，均指向 `72b8e7f`
- remote `origin/main` 也是 `72b8e7f`，无落后
- 工作树干净，Git 层无任何遗留问题

### 已完成 PR (chronological)
| # | Commit | 内容 |
|---|--------|------|
| #10 | `72b8e7f` | fix: remove duplicate entry_points from setup.py |
| #9 | `6b23ec8` | feat: 批量导入进展log和每周老师要求 |
| #8 | `f809335` | fix: add cyan to _RICH_TAG regex for calendar alignment |
| #7 | `42ab1cd` | fix: 练习日历+独立显示、db_path绝对路径、图例格式统一 |

### 遗留
- `STATUS.md` 和 `DEVELOPMENT_PLAN.md` 日期停留在 2026-04-25，内容与现状不符（下次需要更新）
- **配置管理 TUI**：曾在某次 session 讨论过，但 context 压缩丢失了细节，下个 session 需重新确认需求

### 未完成功能（待重建）
- **配置管理 TUI**：功能内容和进度不明，需在下个 session 重新确认

---

## 2026-01-28 (已归档数据)

项目 | 金额
-----|------:
节拍器 | 147
lingokids | 545
很久以前羊肉串 | 549
竹笛考级 | 284
洗车会员费 | 6820
海南租车 | 2533 (原记录 2522+132=2654? 待核实)
萨莉亚+弹珠 | 207 (原记录 75+853? 待核实)
元旦云南土菜吃饭 | 853
**合计** | **12,079**
