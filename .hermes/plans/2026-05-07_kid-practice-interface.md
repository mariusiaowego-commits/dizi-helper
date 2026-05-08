# 儿童竹笛练习助手界面 — 执行计划

## 目标

为7岁女儿构建简单、有趣的竹笛练习使用界面，让她能在 iPad/iPhone 上独立完成：
1. 练习前准备检查
2. 练习打卡/记录/查看报告
3. 游戏化签到激励
4. 成就海报生成（爸爸手动触发）

---

## 现状

- dizical CLI 运行在本地 macOS，无移动端界面
- 数据库：SQLite（dizical.db 存练习数据）
- 练习数据：daily_practices, practice_items, practice_categories, teacher_requirements
- 已有 dizical practice report 调用 Hermes image generation 生成月报图片

---

## 架构方案

**选型：本地 Web 服务器（FastAPI + HTML/JS）**

原因：
- iPad Safari 直接访问，无需安装 App
- Python FastAPI 在本机运行，CLI/db 直连，无数据同步
- 可复用现有 Hermes image generation
- 比 TUI 对7岁儿童更友好（大按钮、大字体、颜色图形）

**服务端口**：默认 localhost:8765

---

## 功能模块

### 模块1：练习准备界面（/prepare）
入口：打开 App 第一个看到的页面

显示内容：
- 🎵 今日练习准备清单（大字、图形化）
  - [ ] 谱架摆好了吗？
  - [ ] 小镜子竖好了吗？
  - [ ] 笛膜贴好了吗？
- 📋 本周老师要求（从 teacher_requirements 读当天所在周）
- 💡 昨天小结缺了什么 → 今天建议多练什么

交互：点击"准备好了！开始练习" → 进入练习打卡页面

---

### 模块2：练习打卡（/practice）
简单打卡：选择练习项目 + 时长

界面设计：
- 大按钮网格（每个练习项目一个按钮，图标+大字）
- 点击计时（倒计时或正向计时）
- 完成后点"打卡"
- 一句话进展录入

---

### 模块3：我的成就（/achievements）
显示：
- 🔥 连续打卡天数（大字火焰数字）
- ⭐ 总练习时长
- 🏆 已获得成就徽章
- 本周目标进度

---

### 模块4：练习报告（/report）
查看：
- 月历热力图（颜色深浅=练习时长）
- 周/月的练习数据柱状图
- 老师要求完成率

---

### 模块5：成就海报生成（/praise）
爸爸界面（需密码保护）：
- 选择成就类型：
  - 🌟 连续打卡（7天/30天）
  - 👏 老师表扬
  - 💪 爸爸觉得练得不错
  - 📅 月度目标完成
- 填入自定义鼓励语
- 点击生成 → 调用 Hermes image generation → 展示并保存

---

## 文件结构

src/kid_app/
  __init__.py
  app.py           # FastAPI 主应用
  routes/
    prepare.py
    practice.py
    achievements.py
    report.py
    praise.py
  templates/
    prepare.html
    practice.html
    achievements.html
    report.html
    praise.html
  static/
    style.css
    app.js
  images.py         # Hermes image generation 调用封装

dizical_kid/
  __init__.py
  cli.py            # dizical_kid start 命令

---

## 实施步骤

### Phase 1：基础框架
1. 创建 src/kid_app/ 目录结构
2. 搭建 FastAPI 基础框架
3. 静态 HTML/CSS 基础样式（iPad 优先，大字体、圆角、鲜艳颜色）
4. dizical_kid start 命令启动服务器

### Phase 2：练习准备页
5. /prepare 路由：从 db 读本周老师要求 + 上周数据
6. 图形化准备清单：大字 + 图形 + 点击确认交互
7. "准备好了"按钮 → 跳转 /practice

### Phase 3：打卡页
8. /practice 路由：列出所有练习项目（大按钮网格）
9. 点击项目 → 计时器（5/10/15/20分钟档位）
10. 计时结束 → 打卡确认 → 写 db

### Phase 4：成就页
11. /achievements 路由：读打卡数据，算连续天数/总时长/徽章
12. 图形化徽章展示

### Phase 5：海报生成
13. /praise 路由：选择类型 → 调用 Hermes image generation
14. 海报保存到 data/reports/

### Phase 6：报告页
15. /report 路由：月历热力图 + 柱状图（纯 CSS/JS）

---

## 关键实现细节

### Hermes 图片生成
MILESTONE_PROMPTS = {
    "streak_7": "A celebratory badge for a 7-day practice streak...",
    "streak_30": "A gold trophy illustration for 30-day streak...",
    "teacher_praise": "A cheerful illustration with text {custom_message}...",
    "dad_praise": "A warm encouraging card with {custom_message}...",
    "monthly_goal": "A monthly achievement certificate...",
}

### 数据读取复用
from src import practice, database as db

def get_today_assignment():
    today = dt.date.today()
    week_start = today - dt.timedelta(days=today.weekday())
    return db.get_weekly_assignment(week_start)

---

## 风险与取舍

| 风险 | 应对 |
|------|------|
| iPad Safari 访问本地 macOS | 启动时显示 IP:PORT，同一局域网访问 |
| 7岁女儿误操作改数据 | 女儿界面只读/打卡，爸爸界面需 PIN |
| 图片生成质量不稳定 | 先用固定模板提示词，后续按需调优 |

---

## 验证步骤

# 启动服务
dizical_kid start
# iPad Safari 打开 http://localhost:8765

# 测试各页面
curl http://localhost:8765/prepare
