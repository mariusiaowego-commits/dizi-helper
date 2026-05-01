# dizical-report prompt 参数化方案

## 任务
将 dizical-report skill 的 image prompt 拆分为「静态风格模板」+「动态数据注入」，支持多风格可配置。

## 方案

### prompt 结构

```
[STATIC] 开头描述 + 视觉风格要求
[DATA]    本月数据（JSON直接嵌入）
[STATIC] 布局要求（包含数据字段说明）
```

### 静态部分（不变，每次复用）

```python
STYLE_TEMPLATE = """创作一张关于「竹笛练习月报」的可视化信息图，目标是帮助用户直观了解：本月练习概况、各项练习时长分布、每周练习进展、练习亮点与待改进点。

画面要像高质量数学讲义 + 手绘教育海报，优雅、清晰、信息丰富，但不要杂乱。

视觉风格：
- 竖版或横版均可，干净的浅色纸张背景
- 深蓝标题，黑色/深灰正文线条
- 少量优雅的蓝色、青绿色、金色、红色强调色
- 圆角卡片、细线边框、编号标签、手绘箭头、局部放大框和总结栏
- 整体要美观、平衡、有学术感，让人一眼看懂这个月练习得怎么样"""

LAYOUT_TEMPLATE = """请将以上数据转化为信息图布局，包含：
1. 标题区：{year}年{month}月练习月报
2. 核心指标卡：总练习时长{total_minutes}分钟、练习天数{practice_days}/{total_days}天
3. 各项练习时长分布（横向柱状图风格的手绘图表）：{item_bar_chart}
4. 每周练习时长趋势（{n}周：{week_mins}分钟）
5. 总结栏"""

DATA_FIELDS = """数据说明：
- total_minutes: 本月总练习时长（分钟）
- practice_days: 有练习的天数
- total_days: 当月总天数
- item_totals: 各项练习时长 {"项目名": 分钟, ...}
- weeks: 每周汇总列表，每周total_minutes和practice_days"""
```

### 动态注入函数

```python
def build_prompt(year, month, data):
    item_bars = "、".join(f"{k}{v}分钟" for k, v in data['item_totals'].items())
    week_mins = "、".join(str(w['total_minutes']) for w in data['weeks'])
    layout = LAYOUT_TEMPLATE.format(
        year=year, month=month,
        total_minutes=data['total_minutes'],
        practice_days=data['practice_days'],
        total_days=data['total_days'],
        item_bar_chart=item_bars,
        n=len(data['weeks']),
        week_mins=week_mins
    )
    return f"{STYLE_TEMPLATE}\n本月数据（JSON）：{json.dumps(data, default=str)}\n{layout}\n{DATA_FIELDS}"
```

## 多风格可配置

预设风格模板（用户通过参数选择）：

| style | 风格名 | 描述 |
|-------|--------|------|
| academic | 数学讲义风 | 深蓝标题、浅纸底、少量青绿/金色点缀（当前这条） |
| cute | 卡通可爱风 | 圆胖字体、彩虹配色、动物图标 |
| minimal | 简约商务风 | 黑白灰、几何图形、无装饰 |
| vintage | 复古海报风 | 旧纸张纹理、衬线字体、手绘线条 |

```python
STYLES = {
    "academic": STYLE_ACADEMIC,
    "cute": STYLE_CUTE,
    "minimal": STYLE_MINIMAL,
    "vintage": STYLE_VINTAGE,
}

def build_prompt(year, month, data, style="academic"):
    style_template = STYLES.get(style, STYLES["academic"])
    # ... 同上
```

用户通过 `dizical-report --style academic` 或自然语言「生成卡通风格的3月练习报告」选择。

## 交付物

1. 修改 `/Users/mt16/.hermes/skills/dizical-report/SKILL.md` - 将 prompt 模板参数化
2. 修改 `dizical` CLI - `practice report` 命令增加 `--style` 参数
3. 实现 `build_prompt()` 函数，支持多风格切换

## 参考

刚验证有效的风格（2026年3月）：academic
图片：https://v3b.fal.media/files/b/0a984711/9J84H0IbiYJIM3fpqbWbp_8lfctMfJ.png
