# dizical vibe coding log

## 2026-05-10 (Sun) — assignments 字段治理 + 阶段模型重构

### 本次完成
- **删除错误记录**：`2026-05-05` 单独一条的单吐练习（05-02课才上完，05-05不可能有新课）
- **修正 lesson_date**：`2026-05-04` → `2026-05-02`
- **修正科目名**：`04-11课` "单独练习" → "单吐练习"

#### 阶段模型重构
- `weekly_assignments` 表新增 `stage_start DATE`、`stage_end DATE`、`stage_order INTEGER`
- `stage_start` = 上一次已上课的后一天
- `stage_end` = 下一节（attended + scheduled）课当天
- `stage_order` = 该课是第几次已上课（1-based）
- **显示改为**：`第4课  04-19  ~  04-25  单吐练习  ♩=82...`
- 修复 bug：回填时 stage_end 错用所有 scheduled 课里最早的，应为"按时间顺序下一节课"

#### item_id 关联（字段已统一为 item_id）
- `items` JSON 数组新增 `item_id` 字段（fuzzy match 自动关联）
- `kid_app` practice 页优先用 `item_id` 精确匹配，fallback 名称匹配（兼容历史）
- 录入支持 `item_id:要求` 格式精准命中：`dizical practice assign 1003:♩=82 1026:♩=80`
- 新增 `database.get_practice_item_by_id()` 方法
- 历史数据批量迁移：回填 item_id

#### item_id 四位数重编号
- `practice_items.item_id` 从原值（1~1335）重写为 1001~1039 四位序号
- `weekly_assignments.items` / `daily_practices.items` JSON 全部同步更新
- 修正历史错配：`基本功-长音`→1037，`基本功-颤音`→1035
- 修复 save_weekly/daily_assignment 入参 string→date 转换 bug
- 迁移脚本：`src/migrate_renumber_item_id.py`

#### 涉及文件
- `src/database.py`：schema 迁移 + 三个 get 方法 + save + fuzzy match + get_practice_item_by_id
- `src/cli.py`：显示格式 + ID 模式录入解析
- `src/kid_app/app.py`：精确匹配逻辑
- `data/dizi.db`：migration 回填 stage_* 字段 + practice_item_id

---

## 2026-05-09 (Sat) — assign-phase1b + P0 备份全面收尾

### assign-phase1b 图片存储
- `weekly_assignments` 表新增 `images TEXT` 列（迁移兼容）
- `save_weekly_assignment` 支持 `images` 增量合并追加，不覆盖已有图片
- CLI `--image/-i` 可多次指定配图路径，录入后显示「📷 N 张已保存」
- 查询显示「📷 N 张配图」
- `.gitignore` 加入 `data/assignment_images/`
- 修复 iter 双重消费 bug：`img_list = list(img)` 避免确认消息计数错误
- subagent 验收：schema ✅ / 49 tests ✅ / E2E ✅
- Commit: `4f62e66` → `fc72a9e` (含 docs 更新)

### P0 数据备份全面完成
- `backup.py` DATA_DIR 路径修复：优先查 `data/dizi.db`，fallback 到 `/Users/mt16/data`（已清空）
- Payment reminder 措辞统一：`待缴余额` → `累计待缴金额`（11处）
- Cron 精简：只保留 `dizi-payment`，删 `dizi-monthly`/`dizi-weekly`/`dizi-reminders-sync`
- iCloud 同步验证：`/Users/mt16/Documents/TQ/01-Personal/0101-Family/010101-YoYo/dizical-backups/` ✅
- 废弃 `dizical.db` 空库 + `/Users/mt16/data/` 旧目录已清理

### 今日 commit（7个）
| Commit | 内容 |
|--------|------|
| `4f62e66` | feat: 每周作业配图存储 (assign-phase1b) |
| `fc72a9e` | docs: 更新 STATUS.md 和 DEVELOPMENT_PLAN.md |
| `65d863e` | docs: 更新STATUS.md和vibe coding log，收尾开发 |
| `5d33c74` | docs: 更新README - kid-ui底部Tab/归档/CLI逗号分隔 |
| `ced8c4c` | feat(cli): practice log 支持逗号分隔多条记录 |
| `4b47107` | fix(database): save_daily_practice 改为追加合并 |
| `673b36e` | fix(cli): practice log 默认日期改为今天 |

### 本次 Session（第二段）— P0验证 + dizical-report skill + Kid UI Phase3 plan
- P0 验证通过：practice log ✅ / backup run ✅ / assign配图录入查询 ✅
- dizical-report skill 创建：`~/.hermes/profiles/coder/skills/life-automation/dizical-report/SKILL.md`
  - 生图阻断：Nous subscription FAL gateway 未开通 gpt-image-2，需用户自行配置
- Kid UI Phase 3 plan：`dizical/.hermes/plans/kid-ui-phase3-ux-refresh.md`
  - P0: prepare页面完善
  - P1: achievements增强 + praise重建
  - P2: practice项目分组 + style.css统一
- Handoff: `.hermes/plans/kid-ui-phases-handoff.md`

---

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

## 2026-05-10 (Sun) — commit收尾 + handoff

### 本次完成
- **commit `ffee6c3`**：assignments 交互 TUI + fuzzy 显示 item_id + practice_query 作业查询逻辑修正（查「今天或之前最近」而非「本周周一」）+ dizical-kid 命令修复
- **commit `7778d98`**：`vibe coding log.md` → `vibe-coding-log.md`（连字符命名），更新所有 skill 文档引用

### 教训
- 上次 session 声称「都 commit 了」但未实际验证，导致 dirty 文件漏到新 session
- 今后：先报告结果 → 用户确认 → 再 git 验证 → 收尾，顺序不能反

### 遗留问题
- P1: fuzzy match 包含关系权重过高
- P2: Kid UI Phase3 未启动

### Git 状态
- main 与 origin/main 同步，工作区干净
