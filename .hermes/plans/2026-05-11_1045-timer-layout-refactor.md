# 计划：practice.html 三栏布局重构

**目标**：按 PRD `PRD-计时器模块重构-260511.md` 实现左-中-右三栏布局。
**文件**：`src/kid_app/templates/practice.html`

---

## 当前状态

现有布局是**垂直堆叠**：
1. 顶部：今日已练习 X 分钟 + 时钟
2. timer-card（计时器，含时间按钮/开始/提前结束/确认区域/快速录入/额外练习时间）
3. 选择练习项目（4列网格）
4. 今日练习记录

PRD 要求改为**三栏 + 底部科目网格**：
```
┌─────────────────────────────────────────────┐
│  [今日已练习: X 分钟]          [实时时钟]    │
├──────────┬────────────────────┬────────────┤
│ 🎯老师要求│      ⏱️ 计时器      │ 🌿额外练习  │
│          │                    │            │
│  (选中后 │   [  00:00  ]      │ +5/10/15   │
│   显示)  │  [5][10][15][20][30]│ +20/+30   │
│          │  [开始] [提前结束]  │ [输入][添加]│
│          │                    │  记录列表... │
│          │  [快速录入面板]    │            │
├──────────┴────────────────────┴────────────┤
│         选择练习项目（4列色块网格）           │
├─────────────────────────────────────────────┤
│              📋 今日练习记录                  │
└─────────────────────────────────────────────┘
```

---

## 重构步骤

### Step 1：提取现有 JS 逻辑（只读分析）

从现有 `practice.html` 提取：
- `selectedItem`、`selectedDuration`、`quickDuration` 状态
- `toggleTimer()` / `startTimer()` / `stopTimer()` / `finishEarly()` / `finishTimer()`
- `submitPractice()` / `submitQuickLog()`
- `addExtraMins()` / `addExtraFromInput()` / `deleteExtraRecord()`
- `loadTodayRecords()` / `renderTodayRecords()` / `deleteRecord()`
- `selectItem()` / `renderItems()` / `renderArchivedItems()`
- `refreshExtraSection()`
- `ENCOURAGEMENTS` / `_daily_encouragement()`

> 全部 JS 逻辑保留，不改动，只重组 HTML 结构。

### Step 2：重写 HTML 结构（三栏）

保留 `<style>` 和 `<script>` 块，只替换 `<body>` 内的 HTML：

```
<div class="top-bar">...</div>
<div class="timer-layout">
  <div class="panel panel-req">   ← 左栏 25%
  <div class="panel panel-center"> ← 中栏 45%（主计时器）
  <div class="panel panel-extra"> ← 右栏 30%（额外时间）
</div>
<div class="item-section">
  <div class="section-label">选择练习项目</div>
  <div class="item-grid">...</div>
  <button class="archived-toggle">...</button>
  <div class="archived-section">...</div>
</div>
<div class="card today-records">...</div>
```

### Step 3：重写 CSS（三栏布局）

新增 `.timer-layout` / `.panel` / `.panel-req` / `.panel-center` / `.panel-extra` 样式，覆盖或替换原有的：
- `#reqTip` → `.panel-req` 内联
- `.quick-add-section` / `.extra-section` → `.panel-center` / `.panel-right` 子元素
- `.timer-big` → `.timer-display`（移入 panel）
- 整体字号放大（见 PRD：body 20px，左栏内容 16px，计时器 72px）

### Step 4：调整 JS 函数 DOM 引用

因为 DOM 结构变化，以下 ID 可能改变：
- `#timer-card` → `#timerPanel` 或直接是 `.panel-center`
- `#confirmArea` → 同上（panel-center 内）
- `#quickAddSection` → panel-center 内
- `#extraSection` → panel-extra
- `#extraLogList` → panel-extra 内
- `#reqTip` → panel-req 内

函数内部 DOM 查询 `getElementById` 基本不变（ID 还在），但需确认：

| 函数 | 变化 |
|------|------|
| `selectItem()` | 现在同时控制左栏 req 显示 |
| `refreshExtraSection()` | 目标 DOM 换到 panel-extra |
| `toggleTimer()` / `finishEarly()` | 确认区域 DOM 结构变化 |
| `renderItems()` | 输出不变，结构稳定 |

### Step 5：响应式

```css
@media (max-width: 640px) {
  .timer-layout { grid-template-columns: 1fr; }
}
```

---

## 文件改动清单

| 文件 | 改动 |
|------|------|
| `src/kid_app/templates/practice.html` | 重写 HTML 结构 + CSS + 最小 JS 适配 |

**无后端改动**，纯前端重构。

---

## 验收标准

1. iPad Safari 竖屏：三栏正常显示，无溢出
2. 计时器流程：选科目 → 选时间 → 开始 → 提前结束 → 打卡 → 记录出现
3. 额外练习时间：+N 按钮 + 自定义输入 + 删除二次确认
4. 快速录入：展开 → 选时间 → 直接打卡
5. 老师要求：选中带要求科目 → 左栏显示；无要求科目 → 左栏空态
6. 今日记录：打卡后立即出现
7. pytest 通过（无后端改动，跳过）
