# 🎵 竹笛学习助手 (dizi-helper)

竹笛课程管理 + 缴费提醒 + 统计助手，支持 Telegram + Apple Reminders 双通道交互。

## 功能特性

### 📚 课程管理
- 自动生成每月课程计划（每周六 17:15）
- 节假日自动识别和冲突标记
- 支持添加、取消、调课、确认上课操作
- 完整的课程状态管理

### 💰 缴费管理
- 自动计算每月应缴金额（600元/节，现金）
- 智能缴费提醒（每月最后一课前2天）
- 缴费记录管理和查询
- 待缴余额计算

### 📊 统计报表
- 月度、季度、年度统计
- 课程状态统计
- 财务统计

### ⚙️ 技术架构
- **数据模型**: Pydantic (类型安全)
- **数据库**: SQLite (内置)
- **CLI界面**: Typer + Rich (美化输出)
- **节假日**: chinese-calendar (中国节假日库)

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 开发安装（可使用 dizi 命令）
pip install -e .
```

## 使用方法

### 课程管理

```bash
# 生成5月课程计划
dizi lesson generate 2026-05

# 列出本月课程
dizi lesson list

# 列出指定月份课程
dizi lesson list 2026-05

# 添加课程
dizi lesson add 2026-05-03

# 取消课程
dizi lesson cancel 2026-05-03

# 调课
dizi lesson reschedule 2026-05-03 2026-05-10

# 确认已上课
dizi lesson confirm 2026-05-03
```

### 缴费管理

```bash
# 查看当前月份缴费状态
dizi payment status

# 查看指定月份缴费状态
dizi payment status 2026-05

# 记录缴费1800元（现金）
dizi payment record 1800

# 查看缴费历史
dizi payment history
```

### 统计报表

```bash
# 本月统计
dizi stat monthly

# 季度统计
dizi stat quarterly

# 年度统计
dizi stat yearly
```

## 项目结构

```
dizi-helper/
├── src/
│   ├── __init__.py
│   ├── models.py          # 数据模型 (Pydantic)
│   ├── database.py        # SQLite 操作封装
│   ├── lesson_manager.py  # 课程管理核心逻辑
│   ├── payment.py         # 缴费计算逻辑
│   ├── holiday.py         # 节假日识别
│   └── cli.py             # Typer CLI 入口
├── data/                  # SQLite 数据文件 (.gitignore)
├── tests/
│   ├── test_lesson.py
│   ├── test_payment.py
│   └── test_holiday.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── setup.py
├── DEVELOPMENT_PLAN.md
└── README.md
```

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行指定测试文件
python -m pytest tests/test_lesson.py -v
```

## 配置

复制 `.env.example` 为 `.env` 并修改配置：

```env
# 默认课程配置
DEFAULT_FEE=600
DEFAULT_TIME=17:15
DEFAULT_WEEKDAY=5  # 0=周一, 5=周六

# 数据库配置
DB_PATH=data/dizi.db
```

## 业务规则

1. **上课时间**: 每周六 17:15
2. **学费**: 600元/节，现金支付
3. **缴费时间**: 每月最后一次上课时缴清当月费用
4. **节假日**: 自动标记节假日冲突，提醒用户确认

## 开发计划

- [ ] Telegram Bot 通知集成
- [ ] Apple Reminders 同步
- [ ] Obsidian Markdown 导出
- [ ] Cron 任务自动执行
- [ ] Web 界面

## License

MIT
