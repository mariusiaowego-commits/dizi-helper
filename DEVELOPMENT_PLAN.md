# 🎵 竹笛学习助手 dizi-helper - 开发计划

## 📋 项目概述
竹笛课程管理 + 缴费提醒 + 统计助手，支持 Telegram + Apple Reminders 双通道交互。

**作者**: mtt
**创建时间**: 2026-04-25

---

## 🎯 核心功能

### 1. 课程管理
- **默认规则**: 每周六 17:15 上课
- **支持操作**: 添加、取消、调课、确认上课
- **节假日自动识别**: 使用 `chinese-calendar` 库，自动标记国定假日并提醒确认

### 2. 缴费管理
- **学费**: 600元/节，**只收现金**
- **缴费时间**: 每月最后一次上课时缴清当月费用
- **智能提醒**: 自动计算当月最后一个上课日，提前2天提醒

### 3. 通知系统
- **Telegram Bot**: @hermes_for_mtt_bot (用户后续配置)
- **通知类型**:
  - 每月1日: 本月课程计划 + 节假日冲突提醒
  - 每周六 09:00: 当日上课确认提醒
  - 每月最后一课前2天: 缴费提醒
  - 每次上课当天 21:00: 上课确认 + 缴费标记

### 4. Apple Reminders 双向同步
- **监控列表**: `dizi`
- **检查频率**: 每小时一次
- **支持指令解析**:
  - `取消 5月9日` → 取消课程
  - `加课 5月16日` → 添加课程
  - `缴费 1800` → 记录缴费1800元
  - `改时间 5月9日 到 5月16日` → 调课

### 5. 统计报表
- 本月/季度/年度统计
- 支持导出 Markdown 到 Obsidian
- 路径: `/Users/mt16/Library/Mobile Documents/iCloud~md~obsidian/Documents/`

---

## 🏗 技术栈

```
Python 3.10+
├── pydantic + pydantic-settings  # 数据模型 + 配置
├── sqlite3                       # 数据库 (内置)
├── typer + rich                  # CLI + TUI 界面
├── python-telegram-bot[v20]      # Telegram 通知
├── chinese-calendar              # 中国节假日识别
└── remindctl (CLI)               # Apple Reminders 集成
```

---

## 📁 项目结构

```
dizi-helper/
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydantic 数据模型
│   ├── database.py            # SQLite 操作封装
│   ├── lesson_manager.py      # 课程管理核心逻辑
│   ├── payment.py             # 缴费计算逻辑
│   ├── holiday.py             # 节假日识别
│   ├── notifier.py            # Telegram 通知封装
│   ├── reminders.py           # Apple Reminders 同步 + 指令解析
│   ├── obsidian.py            # Obsidian Markdown 导出
│   └── cli.py                 # Typer CLI 入口
├── data/                      # SQLite 数据文件 (.gitignore)
├── tests/
│   ├── test_lesson.py
│   ├── test_payment.py
│   └── test_holiday.py
├── .env.example               # TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
├── requirements.txt
├── pyproject.toml
├── setup.py
├── DEVELOPMENT_PLAN.md        # 本文档
└── README.md
```

---

## 📊 数据库设计

### lessons 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| date | DATE | 上课日期 (YYYY-MM-DD) |
| time | TIME | 上课时间 (HH:MM, 默认 17:15) |
| status | TEXT | scheduled/attended/cancelled |
| fee | INTEGER | 学费 (默认 600) |
| fee_paid | BOOLEAN | 是否已缴费 |
| is_holiday_conflict | BOOLEAN | 是否与节假日冲突 |
| notes | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### payments 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| payment_date | DATE | 缴费日期 |
| amount | INTEGER | 缴费金额 |
| lesson_ids | TEXT | 覆盖的课程 ID (逗号分隔) |
| payment_method | TEXT | 固定为 '现金' |
| notes | TEXT | 备注 |
| created_at | DATETIME | 创建时间 |

### settings 表
| 字段 | 类型 | 说明 |
|------|------|------|
| key | TEXT PK | 配置键 |
| value | TEXT | 配置值 |
| updated_at | DATETIME | 更新时间 |

---

## ⌨️ CLI 命令列表

```bash
# 课程管理
dizi lesson generate 2026-05    # 生成5月课程计划
dizi lesson list                 # 本月课程列表
dizi lesson list 2026-05         # 指定月份
dizi lesson add 2026-05-03       # 添加课程
dizi lesson cancel 2026-05-03    # 取消课程
dizi lesson reschedule 2026-05-03 2026-05-10  # 调课
dizi lesson confirm 2026-05-03   # 确认已上课

# 缴费管理
dizi payment status              # 查看当前应缴状态
dizi payment record 1800         # 记录缴费1800元(现金)
dizi payment history             # 缴费历史

# 统计报表
dizi stat monthly                # 本月统计
dizi stat quarterly              # 季度统计
dizi stat yearly                 # 年度统计

# 提醒系统
dizi remind monthly              # 手动触发本月课程计划通知
dizi remind daily                # 手动触发当日上课确认
dizi remind payment              # 手动触发缴费提醒

# Apple Reminders 同步
dizi reminders check             # 检查'dizi'列表指令
dizi reminders sync              # 双向同步

# Obsidian 导出
dizi obsidian export             # 导出本月报告到Obsidian
```

---

## 🧪 开发阶段计划

### ✅ 第一阶段：核心数据层
- [ ] 数据模型 (models.py)
- [ ] 数据库操作封装 (database.py)
- [ ] 节假日识别 (holiday.py)

### ✅ 第二阶段：业务逻辑层
- [ ] 课程管理核心 (lesson_manager.py)
  - 自动生成某月周六课程
  - 节假日冲突检测
  - 添加/取消/调课/确认
- [ ] 缴费计算逻辑 (payment.py)
  - 计算当月应缴金额
  - 找到当月最后一个上课日
  - 记录缴费

### ✅ 第三阶段：CLI 界面
- [ ] Typer CLI 入口 (cli.py)
- [ ] Rich TUI 美化输出

### ✅ 第四阶段：通知系统
- [ ] Telegram 通知封装 (notifier.py)
- [ ] Apple Reminders 同步 (reminders.py)
- [ ] 指令解析 (自然语言理解)

### ✅ 第五阶段：集成与测试
- [ ] 单元测试
- [ ] Obsidian 导出
- [ ] Cron 任务配置文档
- [ ] README 完整文档

---

## 📝 业务规则细节

### 节假日识别规则
1. 每月1日生成课程计划时，调用 `chinese_calendar.get_holiday_detail()`
2. 如果是节假日，标记 `is_holiday_conflict=True`，notes 填节假日名称
3. 提醒时显示 ⚠️ 标记，等待用户确认

### 缴费提醒逻辑
```python
def get_last_lesson_date(year, month):
    # 找到当月所有周六
    # 过滤已取消的课程
    # 返回最后一个上课日
    return last_saturday

def get_payment_reminder_date(last_lesson_date):
    # 提前2天提醒
    return last_lesson_date - timedelta(days=2)
```

### Reminder 指令解析规则
支持自然语言模糊匹配：
- 包含 "取消" + 日期 → 取消课程
- 包含 "请假" + 日期 → 取消课程
- 包含 "加课" + 日期 → 添加课程
- 包含 "缴费" + 金额 → 记录缴费
- 包含 "改" + 日期 + "到" + 日期 → 调课

---

## 🔧 配置说明

### .env 文件
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=351549096
REMINDER_LIST_NAME=dizi
OBSIDIAN_PATH=/Users/mt16/Library/Mobile Documents/iCloud~md~obsidian/Documents/
DEFAULT_FEE=600
DEFAULT_TIME=17:15
DEFAULT_WEEKDAY=5  # 0=周一, 5=周六
```

### Hermes Cron 任务 (后续配置)
```bash
# 每月1日 09:00 - 生成当月课程计划
0 9 1 * * dizi remind monthly

# 每周六 09:00 - 当日上课提醒
0 9 * * 5 dizi remind daily

# 每天 10:00 - 检查是否该缴费提醒
0 10 * * * dizi remind payment

# 每小时检查 Apple Reminders
0 * * * * dizi reminders check

# 每天 23:00 - 导出 Obsidian 报告
0 23 * * * dizi obsidian export
```

---

## ✅ 验收标准

1. `dizi lesson generate 2026-05` 能正确生成5月所有周六课程，标记劳动节
2. `dizi payment status` 能正确计算应缴金额
3. `dizi reminders check` 能解析 Reminders 中的简单指令
4. 所有单元测试通过
5. 代码有完整的类型注解

---

## 📌 注意事项

- 时区统一使用 Asia/Shanghai (UTC+8)
- 所有日期时间操作使用 datetime.date/datetime.time，避免时区问题
- 数据库操作使用参数化查询，防止 SQL 注入
- 所有对外接口有异常处理和重试机制
- 配置通过 pydantic-settings 统一管理
