# Kid UI Phase 3 — UX Refresh Plan

**创建时间**: 2026-05-09
**目标**: dizical-kid iPad 界面用户体验优化，面向 7 岁用户
**当前阶段**: Phase 2（底部Tab/归档/practice_config TUI）刚完成

---

## 一、现状检查

### 文件结构
```
src/kid_app/
├── app.py              # 主路由，render() 渲染5个页面
├── templates/
│   ├── prepare.html    # 113行，静态检查项 + 本周要求
│   ├── practice.html   # 516行，计时器 + 项目选择
│   ├── achievements.html # 71行，连续天数 + 4格数据 + 徽章
│   ├── report.html     # 108行，月历热力图
│   └── praise.html     # 219行，表扬海报（已下线跳转Hermes）
└── static/style.css    # 全局样式（各页面共享）
```

### 各页面现状

| 页面 | 代码量 | 核心状态 | 已知问题 |
|------|--------|---------|---------|
| prepare | 113行 | 3个静态检查项 + 老师要求 + 建议 | 检查项写死；本周要求可能为空时无提示 |
| practice | 516行 | 计时器 + 30+项目选择 | 项目列表无分类；计时结束有声音但体验单调 |
| achievements | 71行 | 连续天数 + 4格数据 + 徽章 | 徽章少；缺少进度感；数据卡缺标签说明 |
| report | 108行 | 月历热力图 + 点击查明细 | 已有基本功能，较完整 |
| praise | 219行 | AI海报生成（已下线→跳Hermes） | 孩子使用路径断裂，需重新设计 |

---

## 二、建议优化方向

### 🔴 P0 — prepare 页面动态化

**问题**: 3个检查项（谱架/小镜子/笛膜）写死，孩子看久了无感。每次有新准备要求需改代码。

**优化**:
- 检查项改为从数据库读取（`practice_items` 或新增 `prep_checklist` 配置）
- 或者保留静态但加入「每日一句鼓励语」（随机从列表取）
- 本周老师要求为空时显示「暂无老师要求，直接开始练习吧！」

**影响文件**: `templates/prepare.html`, `app.py`

---

### 🟡 P1 — achievements 页面增强

**问题**: 徽章少（只有连续7/14/30天），缺乏进度感和视觉层次。

**优化**:
- 增加「本周目标进度条」（例：本周目标5天，已完成3天 → 60%进度）
- 增加项目里程碑徽章（例：「单吐达人」「采茶达人」按累计时长触发）
- 页面顶部增加「距离下一个徽章还需X天」提示
- 4格数据加明确标签说明（什么算总练习小时，什么是余数）

**影响文件**: `templates/achievements.html`, `app.py`

---

### 🟡 P1 — praise 页面路径重建

**问题**: `POST /api/praise` → 410 Gone → 前端 redirect 到 Hermes。孩子在 iPad 无法独立完成。

**优化（选一）**:
- **方案A（推荐）**: 重设计 praise 页面，改为「成就展示+分享」而非 AI 生成。孩子点「我要表扬」→ 展示当前已解锁徽章 + 一键截图分享
- **方案B**: 搭桥让 iPad 能触发 Hermes 生成（已知路径：redirect 到 Gateway URL）
- **方案C**: 纯本地预设表扬语（无需 AI，孩子点按钮随机显示鼓励语）

**影响文件**: `templates/praise.html`, `app.py`, `src/kid_app/images.py`

---

### 🟢 P2 — practice 页面微调

**问题**: 项目列表30+，无分类，大滚轮对孩子不友好。

**优化**:
- 项目按大科目（category）分组展示
- 常用项目置顶
- 搜索框已有（Phase 2 cc3cd25），继续优化体验

**影响文件**: `templates/practice.html`, `app.py`

---

### 🟢 P2 — 视觉风格一致性

**问题**: achievements.html 大量内联style，其他页面也有不一致。

**优化**:
- 统一到 `static/style.css`，消除内联style
- 统一卡片圆角、颜色变量、字体大小层级
- 统一的表彰色体系（珊瑚红 #FF6B6B / 青绿 #4ECDC4 / 金橙 #FF6B35）

---

## 三、实现顺序建议

```
Phase 3.1 (P0): prepare 页面完善
  → 老师要求为空时的友好提示
  → 每日一句鼓励语（简单随机，无需AI）

Phase 3.2 (P1): achievements 页面增强
  → 进度条 + 项目徽章
  → 徽章距离提示

Phase 3.3 (P1): praise 页面重建
  → 推荐方案A或C

Phase 3.4 (P2): 视觉一致性统一
  → style.css 整理归一
```

---

## 四、约束与注意事项

1. **不破坏已有功能**: 每个页面修改后必须 curl 验证路由正常
2. **iPad 友好**: 所有触摸目标 ≥ 44px，字体 ≥ 18px
3. **纯前端改动为主**: 页面逻辑在 HTML/JS，不涉及 Python 后端（除 praise 重建）
4. **dizical-kid 启动验证**:
   ```bash
   curl http://localhost:8765/prepare
   curl http://localhost:8765/practice
   curl http://localhost:8765/achievements
   curl http://localhost:8765/report
   curl http://localhost:8765/praise
   ```
5. **测试账号**: YoYo，7岁，2年级，有一定iPad操作能力
