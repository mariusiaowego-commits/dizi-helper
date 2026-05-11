# Handoff: dizical Kid UI Phase 3（2026-05-11）

## 状态：已完成 ✅

`main` 分支已 push：
- `f345a5d` — feat(kid-app): Phase3 优化 commit
- `be67c99` — docs: STATUS.md 更新

---

## 根因

前端 `practice.html:774` 的 `onclick="deleteRecord('${it.item_id}')"` 传了**字符串** `"1"`，后端 `app.py:152` 用 `body.get("id")` 也是字符串，传给 `remove_daily_practice_record_by_id(date, item_id)` 后与 DB 中的 `item_id`（**int**）比较：`1 != "1"` → Python True → 过滤永远失败 → 记录删不掉。

---

## 修复内容

| 文件 | 行 | 改动 |
|------|----|------|
| `practice.html` | 774 | `deleteRecord('${it.item_id}')` → `deleteRecord(${it.item_id})` |
| `app.py` | 152 | `body.get("id")` → `int(body.get("id", 0))` |

---

## 待修复（P0/P1）

### P0: fuzzy match 包含关系权重过高
历史 session 遗留。当输入"单吐"时，fuzzy match 对包含"单吐"的宽泛匹配（如"单吐练习"）权重过高，可能导致错误命中。

### P1: Kid UI Phase3 未启动
见 `PRD-kid-interface-v0.1.md`（Obsidian: `tqob/05 Coding/project-dizical/PRD-kid-interface-v0.1.md`）
- P0: prepare 页面完善
- P1: achievements 增强 + praise 重建
- P2: practice 项目分组 + style.css 统一

### 遗留代码问题
`_normalize_items` 在 `remove_daily_practice_record_by_id` 中实际未被使用（被 `get_daily_practice` 返回的原始数据替代），代码冗余，可清理。

---

## 关键文件

- `src/kid_app/templates/practice.html` — 前端
- `src/kid_app/app.py` — 后端 FastAPI
- `src/database.py` — 数据库操作（`remove_daily_practice_record_by_id` 在第 745 行）
- `data/dizi.db` — SQLite 数据库

## DB 当前状态

- `data/dizi.db` 路径：`/Users/mt16/dev/dizical/data/dizi.db`
- 2026-05-11 items: `[{"item": "单吐", "minutes": 10, "item_id": 1}, {"item_id": 2, "item": "采茶扑蝶", "minutes": 10}]`

---

## 调试方法论（见 [[coding-pitfalls#调试方法论]]）

**核心信号**：直接调用 `deleteRecord(1)` 成功 → 后端 OK + JS 函数 OK + UI 更新 OK，不要重查这些，直接查 onclick 渲染结果。

---

## 收尾检查清单

- [x] bug 修复 commit 已 push（`f7e8682`）
- [x] STATUS.md 更新（2026-05-11 + bug 修复 section）
- [x] vibe-coding-log.md 更新
- [x] wiki project-dizical.md 更新（updated + session + 方法论引用）
- [x] wiki index.md 更新日期
- [x] 旧 plan 文件已删除
- [x] 工作区干净
