# dizical kid-app UI/UX Style Guide

> 记录竹笛助手儿童版（iPad Safari）的视觉语言、组件规范和交互模式。
> 维护者：coder agent
> 最近更新：2026-05-11

---

## 1. Design Principles

- **活力色块**（Vibrant & Block-based）：大圆角卡片、饱和色按钮、图标 emoji 丰富视觉
- **儿童友好**：字号偏大（正文 18-20px）、触控区域 ≥44px、高对比度配色
- **单页应用逻辑**：5 个 tab 页面，固定底部导航，不跳转多页面
- **Server-side render + client enhance**：Jinja2 模板生成 HTML，JavaScript 处理交互和动画

---

## 2. Color System

### CSS Variables（style.css）
```css
:root {
  --bg: #FFF8F0;          /* 页面背景：暖白 */
  --card: #FFFFFF;        /* 卡片背景 */
  --primary: #FF6B6B;     /* 主色：珊瑚红 */
  --secondary: #4ECDC4;   /* 次色：青绿 */
  --accent: #FFE66D;      /* 强调：明黄 */
  --text: #2C3E50;        /* 正文色 */
  --text-light: #7F8C8D; /* 次要文字 */
  --streak: #FF6B35;      /* 连续天数：橙红 */
  --success: #27AE60;     /* 成功/绿 */
  --radius: 16px;         /* 统一圆角 */
  --shadow: 0 4px 12px rgba(0,0,0,0.08);
}
```

### 模板级覆盖（inline style）
每个模板有自己的配色策略，通过 inline `<style>` 覆盖全局：

| 模板 | 背景色 | 主色 | 特色 |
|------|--------|------|------|
| prepare | `#FFF8F0` | `#FF6B6B` | ZCOOL KuaiLe 字体 |
| practice | `#FFF8F0` | `#4ECDC4` | 三栏布局、计时器 |
| achievements | `#FFF8F0` | `#FF6B35` | GSAP 数字滚动动画 |
| report | `#FFF8F0` | `#27AE60` | 月历热力图 |
| praise | `#FFF8F0` | `#FF6B6B` | 渐变海报、ZCOOL KuaiLe |

### 科目按钮 5 色轮转
```css
.item-btn:nth-child(5n+1) { background: #00CED1; }  /* 青色 */
.item-btn:nth-child(5n+2) { background: #FF6B9D; }  /* 粉色 */
.item-btn:nth-child(5n+3) { background: #A855F7; }  /* 紫色 */
.item-btn:nth-child(5n+4) { background: #FF9F1C; }  /* 橙色 */
.item-btn:nth-child(5n+5) { background: #10B981; }  /* 绿色 */
/* 选中态：#FF4D6D（深红）+ box-shadow 凸起效果 */
/* 有老师要求的科目：#FFE066（金黄），文字 #5D4037 */
```

### 三栏布局面板色
```css
.panel-req   { background: #FFFDF5; border: 2px solid #F0D060; } /* 左-淡黄 */
.panel-center{ background: #F0FCFC; border: 2px solid #A0D8D0; } /* 中-淡青 */
.panel-extra { background: #F0F9F0; border: 2px solid #A0C8A0; } /* 右-淡绿 */
```

---

## 3. Typography

### 字体
```css
/* 全局默认（正文） */
font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", sans-serif;

/* prepare.html / praise.html 专用 */
font-family: 'ZCOOL KuaiLe', -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
```

### 字号层级
| 元素 | 字号 | 权重 |
|------|------|------|
| 页面标题 h2 | 22-26px | bold |
| 卡片内标题 h3/h4 | 18-20px | bold |
| 正文 | 18-20px | normal |
| 按钮文字 | 16-17px | bold |
| 科目按钮 | 13px | 700 |
| 次要说明 | 13-14px | normal |
| 底部导航 | 16px | normal |
| 时间显示 | 72px | bold |

---

## 4. Layout System

### 页面结构
```
body
  .nav（固定底部，position:fixed，5个tab）
  .card / 页面内容区
  （padding-bottom: 80px 留出底部导航空间）
```

### 底部导航（所有模板统一）
```css
.nav {
  position: fixed; bottom: 0; left: 0; right: 0;
  display: flex; gap: 4px;
  padding: 8px 8px calc(8px + env(safe-area-inset-bottom));
  background: white; box-shadow: 0 -2px 12px rgba(0,0,0,0.1);
  z-index: 100;
}
.nav a {
  flex: 1; min-width: 0;
  padding: 14px 8px !important;   /* !important 覆盖全局 style.css */
  background: transparent; border-radius: 16px;
  font-size: 16px !important;
  display: flex; flex-direction: column; align-items: center; gap: 2px;
}
.nav a.active { background: #FF6B6B; color: white; }
.nav a:active { transform: scale(0.95); }
.nav-icon { font-size: 20px; }
```

### practice.html 三栏布局
```css
.timer-layout {
  display: grid;
  grid-template-columns: 25% 45% 30%;
  gap: 10px;
  align-items: stretch;
}
/* 响应式：max-width:640px 变为单列 grid-template-columns: 1fr */
```

### 卡片
```css
.card {
  background: white;
  border-radius: 16-20px;
  padding: 20-24px;
  margin-bottom: 16-20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
```

---

## 5. Components

### 按钮

**通用 `.btn`**
```css
.btn {
  padding: 12-14px 24-28px;
  border: none; border-radius: 24-30px;
  font-size: 17-18px; font-weight: bold;
  cursor: pointer;
  transition: transform 0.1s;
}
.btn:active { transform: scale(0.96); }
.btn-primary { background: #FF6B6B; color: white; }
.btn-secondary { background: #4ECDC4; color: white; }
```

**科目按钮 `.item-btn`**
```css
.item-btn {
  width: 100%; min-width: 0; height: 56px;
  border: none; border-radius: 16px;
  font-size: 13px; font-weight: 700; color: white;
  display: flex; align-items: center; justify-content: center;
  padding: 0 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  position: relative;
  transition: transform 0.2s ease, filter 0.2s ease;
}
.item-btn:active { transform: scale(0.96); filter: brightness(0.92); }
.item-btn.selected {
  background: #FF4D6D !important;
  box-shadow: 0 4px 0 #C41E3A;
  transform: translateY(-2px);
}
.item-btn.has-req {
  background: #FFE066 !important; color: #5D4037;
  box-shadow: 0 4px 0 #E6A800; transform: translateY(-2px);
}
.item-btn .req-dot { /* 有老师要求的小黄点 */ }
```

**老师要求 tooltip**
```css
.req-tooltip {
  position: absolute; bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%);
  background: #FFE066; color: #333; font-size: 12px; padding: 6px 10px;
  border-radius: 8px; max-width: 180px; text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15); z-index: 10;
  display: none;
}
.item-btn-wrap:hover .req-tooltip { display: block; }
```

**计时器时间档位 `.time-btn`**
```css
.time-btn {
  padding: 10px 16px;
  border: 2px solid #4ECDC4; background: white;
  border-radius: 20px; font-size: 16px; cursor: pointer;
}
.time-btn.selected { background: #4ECDC4; color: white; }
```

### 卡片内数据格
```css
/* achievements 4格统计 */
grid-template-columns: 1fr 1fr;
background: #E8F5E9 / #FFF8E1 / #E3F2FD / #FCE4EC（4色区分）
font-size: 36px bold，底部 label 14px 次要色
```

### 月历（report.html）
```css
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
/* 热力等级 */
.cal-day.low  { background: #E8F5E9; color: #27AE60; }  /* 少量 */
.cal-day.mid  { background: #FFF8E1; color: #F57C00; }  /* 中等 */
.cal-day.high { background: #FFEBEE; color: #FF6B6B; }  /* 充足 */
.cal-day.today { border: 3px solid #FF6B6B; font-weight: bold; }
.cal-day.empty { background: transparent; }
```

### 徽章（achievements）
```css
/* 容器：图片+文字垂直堆叠 */
.badge-wrap { display: inline-flex; flex-direction: column; align-items: center; gap: 8px; margin: 8px 10px; }
.badge-img { width: 80px; height: 80px; object-fit: contain; filter: drop-shadow(...); }
.badge-img:hover { transform: scale(1.08); }
.badge-label { font-size: 12px; font-weight: 600; padding: 4px 12px; border-radius: 20px; }
.badge-label.flame  { background: #FFF0E0; color: #c56000; }
.badge-label.star   { background: #FFF8DC; color: #b8860b; }
.badge-label.star2  { background: #E8F5E9; color: #2E7D32; }
.badge-label.strong { background: #E3F2FD; color: #1565C0; }
```

---

## 6. Animations

### GSAP（achievements / report）
```javascript
// achievements 入场：卡片 + 数字滚动 + 徽章依次弹入
gsap.fromTo(streakCard, { opacity: 0, scale: 0.7, y: 30 }, { opacity: 1, scale: 1, y: 0, duration: 0.7, ease: "back.out(2.2)" });
gsap.fromTo(statCards, { opacity: 0, y: 40, scale: 0.9 }, { opacity: 1, y: 0, scale: 1, duration: 0.55, stagger: 0.15, ease: "back.out(1.8)" });
gsap.fromTo(badges, { opacity: 0, scale: 0, y: 50 }, { opacity: 1, scale: 1, y: 0, duration: 0.5, stagger: 0.18, ease: "back.out(2.2)" });

// 数字滚动
let streakCount = 0;
const streakInterval = setInterval(() => {
  streakCount++;
  streakEl.textContent = streakCount;
  gsap.fromTo(streakEl, { scale: 1.15 }, { scale: 1, duration: 0.1 });
  if (streakCount >= streakTarget) { /* bounce */ }
}, 80);
```

### Canvas-Confetti（practice 打卡成功）
```javascript
function fireConfetti() {
  const colors = ['#FF6B6B','#4ECDC4','#FFE066','#FF8CC8','#6BCB77'];
  // 左右对射
  (function frame() {
    confetti({ particleCount: 4, angle: 60, spread: 55, origin: { x: 0 }, colors });
    confetti({ particleCount: 4, angle: 120, spread: 55, origin: { x: 1 }, colors });
    if (Date.now() < end) requestAnimationFrame(frame);
  }());
  // 主射
  confetti({ particleCount: 100, spread: 100, origin: { y: 0.6 }, colors });
}
```

### CSS @keyframes（全局）
```css
@keyframes celebrate {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}
.celebrate { animation: celebrate 0.6s ease 3; }
```

### 触控反馈（通用）
```css
/* 所有可点击元素 */
:active { transform: scale(0.95-0.96); }
/* item-btn 用 filter: brightness(0.92) 替代 transform */
```

---

## 7. External Dependencies

| 库 | 版本 | 用途 | CDN |
|----|------|------|-----|
| GSAP | 3.12.5 | achievements/report 动画 | cdnjs |
| canvas-confetti | 1.9.3 | practice 打卡庆祝动画 | cdnjs |
| html2canvas | 1.4.1 | praise 分享图片生成 | cdnjs |
| ZCOOL KuaiLe | Google Fonts | prepare/praise 标题字体 | Google Fonts |

---

## 8. Known Issues

- **宽屏右边界**：`.panel-extra` 在 iPad Safari 横屏（≥641px）时右边界留白不足，负 margin 方案在部分设备上不稳定，移动端（单列）正常。
- **科目按钮文字对比度**：亮色背景（青色/粉色等）+ 白色文字，部分颜色对比度偏低，但修改后变丑，已回退。

---

## 9. File Map

```
src/kid_app/
  templates/
    prepare.html      # 准备页：检查清单、鼓励语、老师要求
    practice.html     # 练习页：三栏布局（老师要求/计时器/额外练习）+ 科目选择 + 打卡
    achievements.html # 成就页：连续天数、统计数据、徽章展示
    report.html       # 报告页：月历热力图 + 当天练习明细
    praise.html      # 表扬页：每日表扬语 + 徽章 + 分享截图
  static/
    style.css         # 全局样式（CSS variables、通用组件）
    badges/
      fire_badge.png/svg
      medal_badge.png/svg
      star_badge.png/svg
      week_star_badge.png/svg
```
