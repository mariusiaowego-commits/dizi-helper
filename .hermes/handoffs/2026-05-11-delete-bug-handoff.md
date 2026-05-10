# Handoff: dizical-kid 删除功能 Bug（2026-05-11）

## 问题描述
dizical-kid web app（`/practice` 页面）点击 ✕ 删除已添加的练习记录无效——点完记录依然存在。

## 技术背景

### 关键文件
- `/Users/mt16/dev/dizical/src/kid_app/templates/practice.html` — 前端
- `/Users/mt16/dev/dizical/src/kid_app/app.py` — 后端 FastAPI
- `/Users/mt16/dev/dizical/src/database.py` — 数据库操作
- `/Users/mt16/dev/dizical/data/dizi.db` — SQLite 数据库

### 删除相关 API
- `DELETE /api/log` — body: `{"date": "YYYY-MM-DD", "id": item_id}`
- `GET /api/practices/{date}` — 返回 `{"date", "id", "items": [{"item_id", "item", "minutes"}], "total_minutes", "log"}`

### 关键代码位置
- 前端删除函数：`practice.html` 第 799 行 `async function deleteRecord(id)`
- ✕ 按钮渲染：`practice.html` 第 784 行 `onclick="deleteRecord('${it.item_id}')"`
- 后端删除路由：`app.py` 第 147 行 `async def api_delete_log`

---

## 已尝试的修复（均未解决问题）

### 修复1：消除 re-fetch 竞态
**思路**：删除成功后 `loadTodayRecords()` 重新请求 API，HTTP keep-alive 复用连接导致 GET 读到旧数据。

**修复**：后端 DELETE 响应直接返回删除后的最新 items，前端 `deleteRecord` 用它渲染，不 re-fetch。

**文件**：`app.py` + `practice.html`

**结果**：curl 验证删除逻辑正确，但 browser automation 测试仍有问题。

### 修复2：extract render function
把记录列表渲染逻辑提取为 `renderTodayRecords(items, total)`，供 `loadTodayRecords` 和 `deleteRecord` 共用。

---

## 待排查问题

### 核心谜团

**curl DELETE 完全正常**：
```bash
curl -X DELETE http://localhost:8765/api/log \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-05-10","id":1}'
# 返回 {"ok":true,"items":[{"item_id":2,...}],"total_minutes":5}
# DB 确认删除成功
```

**browser console 直接调用 `window.deleteRecord(1)` 有时返回删除前数据**：
```javascript
// console 调用后：
// result={"ok":true,"items":[{"item_id":1,...},{"item_id":2,...}]}  ← 旧数据
// 或
// result={"ok":true,"items":[{"item_id":2,...}]}  ← 正确删除后数据
```

**关键现象**：
1. browser console 直接调 `deleteRecord()` 返回的数据不稳定——有时正确有时不正确
2. 但 curl DELETE 100% 正确
3. 说明问题不在后端删除逻辑，而在于 **browser fetch 请求和 curl 请求的行为不同**

### 可能根因

**猜测1：uvicorn 多 worker 进程**
本地测试可能启动了多个 uvicorn worker 进程。FastAPI/uvicorn 默认多 worker 时每个进程有独立的 Python 解释器和模块状态。
- curl 请求可能被路由到某个"干净"进程 → DELETE 成功
- browser fetch 请求可能被路由到另一个"缓存了旧数据"的进程 → 返回旧数据

**验证方法**：
```bash
# 检查 uvicorn 启动方式
ps aux | grep uvicorn
# 确认是否用了 --workers N 参数
```

**猜测2：browser fetch 实际发出的请求与 curl 不同**
browser console 调 `fetch('/api/log', {method:'DELETE', body:...})` 实际发送的请求可能：
- 带了某种 browser 特有的 header 导致后端行为异常
- 发送时机导致 race condition

**验证方法**：在 `api_delete_log` 里加详细日志，打印收到的完整请求头和 body。

### 建议排查步骤

1. **确认 uvicorn 是否多 worker**：
   ```bash
   ps aux | grep uvicorn
   # 如果有多行，说明是多 worker
   # 修复：重启服务并确认只有单 worker
   ```

2. **加详细请求日志**（`app.py` `api_delete_log` 入口）：
   ```python
   print(f"[DELETE] headers={dict(request.headers)}, body={await request.body()!r}", flush=True)
   ```

3. **单 worker 重启后用 browser console 测试**：
   ```javascript
   // 清除所有缓存
   // 重新打开页面
   // 观察 deleteRecord(1) 的返回
   ```

4. **如果单 worker 后仍然失败**：说明问题在前端 fetch 发送方式，而非后端。

---

## 数据库当前状态

- DB 路径：`/Users/mt16/dev/dizical/data/dizi.db`
- 2026-05-10 可能有测试残留数据
- 服务运行 PID：52862（需确认是否还在）

```bash
# 查看当前数据
sqlite3 /Users/mt16/dev/dizical/data/dizi.db \
  "SELECT date, items, total_minutes FROM daily_practices WHERE date='2026-05-10'"
```

---

## 待办

- [ ] 确认 uvicorn 启动方式（单 vs 多 worker）
- [ ] 加请求日志精确定位 browser DELETE 收到什么
- [ ] 单 worker 重启后 browser console 测试
- [ ] 如果仍失败：在 `api_delete_log` 里把收到的 body 完整打印
- [ ] 最终验证：iPad Safari 真实删除操作

---

## 代码变更摘要

```
src/database.py                     | +54 -XX  remove_daily_practice_record_by_id 等
src/kid_app/app.py                  | +89 -XX  api_delete_log 返回最新 items
src/kid_app/templates/practice.html | +134 -XX renderTodayRecords extract + deleteRecord 修复
```
