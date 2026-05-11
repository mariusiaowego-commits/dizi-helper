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

## 收尾文档
- STATUS.md — 项目根目录
- DEVELOPMENT_PLAN.md — 项目根目录
- vibe coding log — `vibe-coding-log.md`（项目根目录） + Obsidian wiki `projects/project-dizical.md`
- wiki — `hermes-base/projects/project-dizical.md`

## vibe coding log
