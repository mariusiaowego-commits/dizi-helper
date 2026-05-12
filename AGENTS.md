# dizical AGENTS

竹笛课程助手，服务女儿竹笛学习。

## 项目路径
`/Users/mt16/dev/dizical`

## 技术栈
- Python 3.14
- SQLite (dizical.db)
- Web UI (iPad friendly)

## 关键数据模型
- `lesson.status=attended` 不一定有 `daily_practice` 记录
- DB `items` 是 JSON，改记录直接 UPDATE 整个 record 更安全

## 部署信息
- dizical-kid deployed to `~/Library/Python/3.14/bin` (copied from hermes profile path, not pip reinstalled)
- Service runs on port 8765
- Full kid-friendly iPad web UI: prepare/practice/achievements/report/praise pages
- commit 8eae04a pushed to main

## 用户偏好
- 偏好通知简洁，不用客气话
- 喜欢日历视图，倾向轻量方案
- cli命令、profile alcove的chat、gateway三种方式交互

## Cron Jobs
- monthly: 每月1号9点
- weekly: 每周日20点
- payment: 每天10点
- reminders sync: 每天8/18点

## 收尾 Checklist（每次会话结束前必须执行）

```
□ STATUS.md — 本次修改涉及的功能，对应条目是否更新（日期 + 阶段描述）
□ vibe-coding-log.md — 新增当日记录，append 到文件开头
□ handoff-YYYY-MM-DD.md — 完整记录含待办清单，写入项目根目录
□ image-gen.md — 生图 CDN URL + 本地路径追加到 Obsidian tqob/00-Artifacts/
□ Git — 测通后 add → commit → feature branch → PR（未测不推）
□ README — 本次改动需要同步更新文档
□ 服务验证 — curl 两个页面确认 200 OK
□ 用户确认 — 展示最终结果
□ Wiki沉淀 — 发现新模式/踩坑记录/项目惯例，同步到 hermes-base/projects/
```

## 收尾文档
- STATUS.md — 项目根目录
- DEVELOPMENT_PLAN.md — 项目根目录
- vibe coding log — `vibe-coding-log.md`（项目根目录） + Obsidian wiki `projects/project-dizical.md`
- wiki — `hermes-base/projects/project-dizical.md`

## vibe coding log
