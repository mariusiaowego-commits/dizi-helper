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

### 本次 session 补充（12:08 PM）
- **Bug 修复**：`/prepare` 本周作业查不到
  - 根因：家长5/2（周六）录入，存 `week_start_date=2026-05-02`，孩子周一打开 App 查本周一（5/4），精确匹配查不到
  - 修复：新增 `database.get_weekly_assignment_for_week(anchor_date)` 方法，查 ≤ anchor_date 的最近一条记录
  - 改 `kid_app/app.py` 的 `/prepare` 路由调用新方法
  - commit `1e81d04`，已 push 到 `origin/feat/kid-ui-refresh`
- **本周判定逻辑改进**：以"包含今天的那周"为锚点，不再强依赖周一为存储基准
- kid_app 服务端口 8765，重启验证 `curl /prepare` 返回"回娘家"

### 分支
- worktree: `hermes/hermes-3bb46bdd`
- 功能分支: `feat/kid-ui-refresh`（已 push）

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

## 2026-05-07 (Thu)

### 修复 thisweek TypeError bug
- **现象**: `dizical practice thisweek` 报错 `TypeError: string indices must be integers`
- **根因**: `daily_practices.items` 字段存了旧格式 `["单吐练习", "回娘家", ...]`（string list）而非标准格式 `[{item: '单吐练习', minutes: N}, ...]`
- **修复**:
  - `src/database.py`: 新增 `_normalize_items()` 辅助方法，`get_daily_practice` / `get_daily_practices_in_range` 读取时自动 normalize
  - DB: 修复 2026-05-07 那条坏数据
- **PR**: #24 合入 main

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
