# Plan: assign 图片存储

## 目标
支持每周老师要求配图：存图片路径，查询时能看到有没有配图。

## 改动

### 1. database.py
- `weekly_assignments` 表加 `images TEXT DEFAULT '[]'` 字段（已有表，用 ALTER TABLE）
- `save_weekly_assignment` 加 `images` 参数（JSON 数组存路径）
- `get_weekly_assignment` / `get_weekly_assignments_in_range` 返回 images 字段

### 2. .gitignore
- 确保 `data/assignment_images/` 目录被忽略

### 3. cli.py - practice_assign
- 新增 `--image` / `-i` 选项，可多次指定，传入图片路径
- 录入后打印：「配图：X 张」

### 4. cli.py - assignments 查询
- 显示时在备注旁提示「📷 有 X 张配图」

### 5. 创建目录
- `mkdir -p data/assignment_images/`

## 验收
1. `dizical practice assign -d 2026-05-05 单吐练习:♩=82 --image /path/to/photo.jpg`
2. `dizical practice assignments -s 2026-05-05 -e 2026-05-05` 显示「📷 有 1 张配图」
3. 再次追加时 images 不丢失

## 不在此阶段
- OCR 识别
- 图片预览
