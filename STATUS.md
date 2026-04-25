# 🎵 竹笛学习助手 - 当前开发状态

**最后更新**: 2026-04-25 15:25
**当前阶段**: 第一阶段核心开发完成，进入 bug 修复

---

## 📂 项目位置
- **main 分支 (干净)**: `/Users/mt16/dev/dizi-helper/`
- **feature/core 分支 (开发中)**: `/Users/mt16/dev/dizi-helper/.worktrees/core/`
- **Git 模式**: worktree 模式，main 分支保持干净

---

## ✅ 已完成

### 核心模块
- [x] `src/models.py` - Pydantic 数据模型 (Lesson, Payment, Settings)
- [x] `src/database.py` - SQLite 操作封装 (DatabaseManager)
- [x] `src/holiday.py` - 节假日识别 (chinese-calendar 库)
- [x] `src/lesson_manager.py` - 课程管理核心逻辑
- [x] `src/payment.py` - 缴费计算逻辑
- [x] `src/cli.py` - Typer CLI + Rich TUI

### 配置文件
- [x] `requirements.txt` - 依赖清单
- [x] `pyproject.toml` - 项目配置
- [x] `setup.py` - 包配置
- [x] `.env.example` - 环境变量示例
- [x] `.gitignore`

### 测试
- [x] `tests/test_holiday.py` - 14 个测试
- [x] `tests/test_lesson.py` - 21 个测试  
- [x] `tests/test_payment.py` - 14 个测试
- 总计: 49 个单元测试

### CLI 命令可用
```bash
dizi lesson generate 2026-05   # 生成5月课程
dizi lesson list                # 课程列表
dizi payment status             # 缴费状态
dizi --help                     # 帮助
```

---

## 🐛 待修复 Bug

### 1. 节假日识别相关 (4 个测试失败)
**问题**: `chinese_calendar.get_holiday_detail()` API 使用不对
- `get_holiday_name()` 返回 None，即使日期确实是节假日
- 导致节假日状态判断有误（5月2日不是节假日却被标记为冲突）

**可能原因**: chinese_calendar 库 API 可能是 `get_holiday_detail()` 返回的不是 `.name` 属性

### 2. 缴费计算相关 (4 个测试失败)
- `test_confirm_attendance` - 确认上课后状态更新有问题
- `test_reschedule_lesson` - 调课功能测试失败
- `test_payment_balance` - 缴费余额计算不对
- `test_payment_history` - 缴费历史查询问题

### 3. 其他小问题
- 运行 `dizi payment status` 时，"已缴金额: 14400 元" 显示异常（应该是 0）
- 4月课程数为 0 可能也是 bug

---

## 🚀 下一步开发计划（第二阶段）

### 优先级 P0 - Bug 修复
1. 修复 holiday.py 的 chinese_calendar API 调用
2. 修复 payment.py 的余额计算
3. 确保所有 49 个单元测试通过

### 优先级 P1 - 通知系统
4. `src/notifier.py` - Telegram 通知封装
   - 使用 python-telegram-bot v20+
   - 支持文本消息、Markdown 格式
   - Bot token 从配置读取

5. `src/reminders.py` - Apple Reminders 双向同步
   - 调用 `remindctl` CLI
   - 监控 `dizi` 列表
   - 自然语言指令解析（取消/加课/缴费/改时间）

### 优先级 P2 - 导出功能
6. `src/obsidian.py` - Obsidian Markdown 导出
   - 月度报告模板
   - 写入到指定路径

### 优先级 P3 - 提醒调度
7. Cron 任务配置文档
8. 提醒逻辑完善

---

## 🧪 测试命令
```bash
cd /Users/mt16/dev/dizi-helper/.worktrees/core/
python3 -m pytest tests/ -v          # 运行所有测试
python3 -m pytest tests/test_holiday.py::TestHolidayChecker::test_is_holiday_may_day -v  # 单个测试

# 手动功能测试
dizi lesson generate 2026-05
dizi lesson list
dizi payment status
```

---

## 📝 开发规范
- 使用 PEP8 代码风格
- 完整的类型注解 (type hints)
- 每个功能要有对应的单元测试
- 提交信息格式: `feat: xxx` / `fix: xxx` / `chore: xxx`
- Git worktree 模式：功能开发在 `.worktrees/xxx` 分支，测试通过后合到 main

---

## 🔧 环境
- Python 3.12+
- 依赖已通过 `pip install -e .` 安装
- `dizi` CLI 命令已在 PATH 中可用
