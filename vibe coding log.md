# dizical vibe coding log

## 2026-05-08 (Fri) — Kid UI Phase 2

### 本次完成（Phase 2）
- **底部Tab导航**：5个页面全部改为 position:fixed bottom，适合 iPad 单手操作
- **practice_config TUI 重构**：子菜单 while True 自循环，q 逐层返回，消灭死角
- **practice_config 归档菜单**：进菜单显示已归档清单，unarchive 行为修正
- **kid-ui 归档逻辑**：已归档小科目默认隐藏，底部归档区按钮点击后弹窗选择
- **practice log 逗号分隔**：支持 `单吐:7，回娘家:4` 中英文逗号多种格式
- **practice log 默认日期**：从"昨天"改为"今天"，与 practice today 一致
- **save_daily_practice 追加修复**：同日期多次 log 改为合并而非覆盖
- **归档 q 键无效 bug**：_archive_choose 两次 input() 导致第二次读空字符串
- **_category_sort 排序验证**：增加重复 ID 检查 + 完整性覆盖检查
- **代码审查**：subagent 审查发现归档 q 键 bug
- **数据库修复**：05-07 数据被 INSERT OR REPLACE 覆盖，补回 17 分钟记录

### 今日 commit（14个）
| Commit | 内容 |
|--------|------|
| `5d33c74` | docs: 更新README - kid-ui底部Tab/归档/CLI逗号分隔 |
| `ced8c4c` | feat(cli): practice log 支持逗号分隔多条记录 |
| `4b47107` | fix(database): save_daily_practice 改为追加合并而非整体替换 |
| `673b36e` | fix(cli): practice log 默认日期改为今天 |
| `585697e` | fix: _do_archive调用_archive_choose而非已删除的_archive_toggle |
| `290b6a1` | fix(practice-config): 修复归档q键无效+排序验证缺失 |
| `9eeeb01` | refactor(practice-config): 全面重构TUI交互规范 |
| `f546d00` | feat(kid-ui): 固定底部Tab导航 + practice_config归档管理 |

---

## 2026-05-08 (Fri) — Timer Bug

### Timer Bug 修复 (`a90e6f6`)
- **现象**: 选5分钟练习，计时300秒后打卡，记录成300分钟
- **根因**: `elapsed` 是秒，`submitPractice()` 和 `finishEarly()` 直接当分钟用
- **修复**: `submitPractice` 传 `Math.floor(elapsed/60)`，`finishEarly` 显示也转分钟

---

## 2026-05-07 (Thu)

### 每周老师要求导入
- 命令: `dizical practice import-assignments data/imports/import-assignments.csv`
- 结果: ✅ 17 周全部导入成功
- CSV 格式: `WeekStart,Item,Requirement,Notes`（日期格式 `YYYY/M/D`）

### 修复 thisweek TypeError bug
- **现象**: `dizical practice thisweek` 报错 `TypeError: string indices must be integers`
- **根因**: `daily_practices.items` 字段存了旧格式 `["单吐练习", "回娘家", ...]` 而非标准格式 `[{item: '单吐练习', minutes: N}, ...]`
- **修复**: `database.py` 新增 `_normalize_items()` 辅助方法，读取时自动 normalize

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

---

## 2026-01-28 (已归档数据)

| 项目 | 金额 |
|-----|------:|
| 节拍器 | 147 |
| lingokids | 545 |
| 很久以前羊肉串 | 549 |
| 竹笛考级 | 284 |
| 洗车会员费 | 6820 |
| 海南租车 | 2533 |
| 萨莉亚+弹珠 | 207 |
| 元旦云南土菜吃饭 | 853 |
| **合计** | **12,079** |
