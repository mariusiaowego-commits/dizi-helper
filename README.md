# 🎵 dizical

> 竹笛课程管理 + 缴费提醒 + Apple Reminders 双向同步

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/tests-49%20passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/lessons-211%20days%20imported-blue" alt="Lessons">
</p>

## 🤔 为什么叫 dizical？

```
dizi + cal(endar) = dizical
 竹笛    日历        ↓
            发音 ≈ Descartes（笛卡尔）

📅 管它什么哲学，我只要管好我的竹笛课表 🎵
```

---

## ✨ Features

- 📅 **自动排课** - 每周六自动生成课程，节假日冲突检测
- 💰 **缴费管理** - 自动统计欠缴、已缴，最后一节课当天提醒
- 🍎 **Reminders 同步** - 在 Apple Reminders 写自然语言就能操作
- 🔔 **Telegram 通知** - 上课提醒/缴费提醒/月度计划，自动推送
- 📊 **可视化课表** - 表格视图 + ASCII 日历视图
- 📝 **Obsidian 导出** - 自动生成月度学习报告
- 🎵 **练习追踪** - 打卡、统计、热力图、老师每周要求导入
- 🏷️ **大科目/小科目** - 增删改查模式，灵活分类管理，支持模糊匹配打卡
- 📝 **练习进展记录** - 每次打卡可附上详细练习进展
- 🎨 **练习月报图片** - 多模板风格可选，AI 生成信息图

## 🎨 练习月报示例

![2026年3月练习月报](docs/2026-03-练习报告示例.jpg)

> 通过 `dizical practice report` 或 alcove profile 的 dizical-report skill 生成

## 👧 dizical-kid（iPad 儿童界面）

面向 7 岁儿童的竹笛练习助手，支持 iPad Safari 访问。

```bash
# 启动服务
dizical kid start

# iPad 访问
# http://<本机IP>:8765
```

**5 个页面**：`/prepare` 准备页 · `/practice` 练习打卡 · `/achievements` 成就徽章 · `/report` 月报 · `/praise` 表扬页

**底部 Tab 导航**：固定底部，点击反馈，适合 iPad 单手操作

**老科目归档**：已归档的小科目默认隐藏，可点击归档区按钮单独选择

**成就徽章**：连续练习/累计时长达成后自动解锁，共 20 种 Enamel Pin 风格徽章：
- 连击系：`streak_1/3/7/14/30/100`（1天～100天）
- 累计系：`total_60/300/600/1000`（60分钟起）
- 特殊徽章：`first_log` 首次打卡、`double` 双倍练习、`week_champ` 本周冠军、`full_month` 全勤月、`all_items` 全部科目、`night_owl` 夜猫子、`one_breath` 一口气、`comeback` 回归练习、`song_end` 曲目完成
- 排行系：`top1/top2/top3` 练习时长前三

```bash
# 启动儿童界面（CLI 方式也可用）
dizical-kid start
```

---

## 🚀 Quick Start

```bash
# 安装
pip install -e .

# 生成课程
dizical lesson generate 2026-05

# 查看课表
dizical lesson list
dizical lesson calendar

# 同步 Reminders
dizical reminders sync
```

## ⚙️ Configuration

创建 `.env` 文件：

```env
REMINDER_LIST_NAME=dizi
OBSIDIAN_PATH=/Users/mt16/Library/Mobile Documents/iCloud~md~obsidian/Documents/
DEFAULT_FEE=600
DEFAULT_TIME=17:15
DEFAULT_WEEKDAY=5
DB_PATH=data/dizi.db
```

## 📦 Commands

```bash
# 状态监控
dizical status                # 实时监控 kid-app（进程/端口/HTTP/最近练习）

# 课程
dizical lesson list           # 课程表
dizical lesson calendar       # 日历视图
dizical lesson generate 2026-05

# 缴费
dizical payment status        # 缴费状态
dizical payment history       # 缴费历史

# 练习
dizical practice log 基本功:20 单吐:15  # 打卡（空格分隔多条）
dizical practice log 单吐:10，回娘家:4 --log "突破5连吐"  # 逗号分隔多条
dizical practice log -d 2026-05-07 基本功:20  # 补录指定日期
dizical practice today        # 今日练习
dizical practice week         # 本周练习
dizical practice calendar 4   # 4月日历
dizical practice stats 4      # 4月统计
dizical practice items       # 练习项目库
dizical practice category list  # 大科目列表
dizical practice category add 气息练习  # 新增大科目
dizical practice category set-item 单吐练习 基本功  # 归属小科目
dizical practice config         # 增删改查模式管理大科目/小科目
dizical practice import <csv>             # 导入练习时长CSV
dizical practice import_logs <csv>       # 批量导入进展log（Date,Log）
dizical practice import-assignments <csv> # 批量导入每周老师要求（WeekStart,Item,Requirement）
dizical practice assign -d 2026-05-05 1003:♩=82 -i img1.jpg -i img2.jpg  # 精准ID+配图录入
dizical practice assignments             # 交互式浏览每课老师要求（↑↓浏览/Enter展开）
dizical practice report -y 2026 -m 3 --style academic  # 生成月报图片

# 同步
dizical reminders sync        # 同步 Reminders
dizical obsidian export 4     # 导出4月报告
```

## 🏗️ Architecture

```
src/
├── cli.py              # CLI 入口
├── lesson_manager.py   # 课程管理
├── payment.py          # 缴费管理
├── practice.py         # 练习追踪（打卡/统计/导入）
├── practice_config.py  # 大科目/小科目增删改查
├── report_templates.py # 月报 prompt 模板系统（多风格）
├── reminders.py        # Apple Reminders 同步
├── notifier.py         # 通知格式化
├── obsidian.py         # Obsidian Markdown 导出
├── database.py         # SQLite 持久化
├── models.py           # 数据模型
└── kid_app/            # iPad 儿童界面（独立 FastAPI 服务，端口 8765）
    ├── app.py          # 路由：/prepare /practice /achievements /report /praise
    ├── badges_page.py  # 徽章墙路由
    └── templates/      # HTML 模板
```

## 📄 License

MIT
