# dizical — Handoff (2026-05-09)

## 当前状态

- **main 分支**: `0167bc7` — 干净，无 worktree
- **remote**: SSH，正常连接
- **今日完成**: assign-phase1b（配图存储）+ P0数据备份全面修复

---

## 今天完成的工作

### assign-phase1b ✅
- `weekly_assignments` 表新增 `images TEXT` 列
- CLI `--image/-i` 多次配图，查询显示「📷 N 张」
- `.gitignore` 已加 `data/assignment_images/`
- 使用指南.md 已更新（第7行目录、第180行用法）
- 验证：P0测试全通过（practice log / backup run / assign录入查询）

### P0 数据备份修复 ✅
- `backup.py` DATA_DIR 路径优先查 `data/dizi.db`
- Payment reminder 措辞统一为「累计待缴金额」
- Cron 精简：只保留 `dizi-payment`（每天10:00）
- iCloud 同步验证通过
- 废弃 `dizical.db` 空库 + `/Users/mt16/data/` 旧目录已清理

### dizical-report skill ✅
- 路径: `~/.hermes/profiles/coder/skills/life-automation/dizical-report/SKILL.md`
- 数据层完整，prompt 模板已写
- **阻断**: Nous subscription FAL gateway 未开通 `gpt-image-2`，报错 HTTP 401。用户需自行在 `hermes config edit` 调整 `image_gen.provider` 或等 Nous Portal 支持

---

## 下一步: Kid UI Phase 3

Plan 路径: `.hermes/plans/kid-ui-phase3-ux-refresh.md`

### 优先级
| 页面 | 优先级 | 改动 |
|------|--------|------|
| prepare | P0 | 老师要求为空时友好提示；每日一句鼓励语 |
| achievements | P1 | 进度条 + 项目徽章 + 距下一徽章提示 |
| praise | P1 | 推荐方案A：徽章展示 + 截图分享，替代AI生成 |
| practice | P2 | 项目按大类分组 |
| 全局 | P2 | style.css 统一 |

### kid-app 启动
```bash
lsof -i :8765 | grep LISTEN && kill <PID>
cd /Users/mt16/dev/dizical && python3.14 -m src.kid_app start &
# iPad访问: http://<ipconfig getifaddr en0>:8765
```

### 验证命令
```bash
curl http://localhost:8765/prepare
curl http://localhost:8765/practice
curl http://localhost:8765/achievements
curl http://localhost:8765/report
curl http://localhost:8765/praise
```

---

## 环境信息
- DB: `/Users/mt16/dev/dizical/data/dizi.db`
- Python: 3.14 (homebrew)
- dizical CLI 已装在 `~/Library/Python/3.14/bin/`
- 测试账号: YoYo，7岁，2年级

## Cron 任务（唯一）
`dizi-payment` — 每天 10:00，检查缴费提醒
