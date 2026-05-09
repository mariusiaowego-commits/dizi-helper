"""
Migration: practice_items.id → item_id
同时将 weekly_assignments.items 和 daily_practices.items JSON 中的 item 字符串
规范化为包含 item_id 的结构。

执行方式（先 dry-run 验证，再正式执行）：
  python3.14 -m src.migrate_item_id --dry-run
  python3.14 -m src.migrate_item_id

回滚：
  cp data/backups/dizi_daily_YYYYMMDD_HHMMSS.db data/dizi.db
"""

import argparse
import json
import sqlite3
import shutil
import sys
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dizi.db"
BACKUP_DIR = Path(__file__).resolve().parent.parent / "data" / "backups"


# ─── Fuzzy matcher (与 database.py 保持一致) ─────────────────────────────────

# 已知非科目标签（泛化标签不是练习科目，不创建 item_id）
SKIP_ITEMS = {
    "要求", "作业", "作业1", "作业2", "大课", "上课", "寒假作业",
    "考级", "无", "准备", "备注", "重点", "提示",
}
# 不应自动创建为 practice_items 的占位/状态类条目
AUTO_CREATE_BLACKLIST = {
    "病假", "上课", "休息", "未练", "请假", "早课", "晚课", "补课",
    "单练", "齐练", "迟到", "早退", "缺席",
}


def fuzzy_match_item_id(item_name: str, items: list) -> tuple:
    """返回 (item_id, item_name) 或 (None, None)"""
    name_map = {it["name"]: it["item_id"] for it in items}

    # 精确匹配
    if item_name in name_map:
        return name_map[item_name], item_name

    # 子串匹配
    for pi_name, pid in name_map.items():
        if pi_name in item_name:
            return pid, pi_name
        if item_name in pi_name:
            return pid, pi_name

    # 模糊匹配
    best_ratio, best_pid, best_name = 0, None, None
    for pi_name, pid in name_map.items():
        r = SequenceMatcher(None, item_name, pi_name).ratio()
        if r > best_ratio and r > 0.6:
            best_ratio, best_pid, best_name = r, pid, pi_name
    return best_pid, best_name


# ─── 迁移函数 ─────────────────────────────────────────────────────────────────

def migrate_practice_items(conn: sqlite3.Connection) -> dict:
    """
    重命名 practice_items.id → item_id。
    SQLite 没有 RENAME COLUMN，用重建表实现。
    """
    cursor = conn.cursor()
    stats = {"rows": 0, "id_values": []}

    # 读取旧数据
    cursor.execute("SELECT * FROM practice_items")
    rows = cursor.fetchall()
    # sqlite3.Column objects → column names via .name attribute
    col_names = [d[0].name if hasattr(d[0], 'name') else d[0][0] for d in cursor.description]
    stats["rows"] = len(rows)
    stats["id_values"] = [dict(zip(col_names, r))["id"] for r in rows]

    # 重建表
    cursor.execute("DROP TABLE IF EXISTS practice_items_new")
    cursor.execute("""
        CREATE TABLE practice_items_new (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            category_id INTEGER REFERENCES practice_categories(id),
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_archived BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO practice_items_new (item_id, name, category_id, sort_order, is_active, is_archived, created_at)
        SELECT id, name, category_id, sort_order, is_active, is_archived, created_at FROM practice_items
    """)
    cursor.execute("DROP TABLE practice_items")
    cursor.execute("ALTER TABLE practice_items_new RENAME TO practice_items")

    # 更新外键引用
    cursor.execute("PRAGMA foreign_keys = off")
    cursor.execute("""
        UPDATE practice_items
        SET category_id = NULL
        WHERE category_id NOT IN (SELECT id FROM practice_categories)
        AND category_id IS NOT NULL
    """)
    cursor.execute("PRAGMA foreign_keys = on")

    conn.commit()
    return stats


def migrate_weekly_assignments(conn: sqlite3.Connection, dry_run: bool = False) -> dict:
    """
    将 weekly_assignments.items JSON 中的字符串条目规范化为 {item_id, item, requirement}。
    同时修复已有的 practice_item_id → item_id。
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, lesson_date, items FROM weekly_assignments")
    rows = cursor.fetchall()

    # 构建 practice_items 字典
    cursor.execute("SELECT item_id, name FROM practice_items")
    pi_map = {row["name"]: row["item_id"] for row in cursor.fetchall()}

    stats = {"total": 0, "migrated": 0, "unmatched": [], "unmatched_items": []}

    for row in rows:
        assignment_id, lesson_date, items_json = row["id"], row["lesson_date"], row["items"]
        if not items_json:
            continue

        try:
            items = json.loads(items_json)
        except (json.JSONDecodeError, TypeError):
            stats["unmatched_items"].append(f"assignment_id={assignment_id}: JSON解析失败")
            continue

        if not isinstance(items, list):
            continue

        new_items = []
        changed = False
        for entry in items:
            stats["total"] += 1
            if not isinstance(entry, dict):
                continue

            # 已有 item_id（之前存的 practice_item_id）→ 重命名为 item_id
            if "practice_item_id" in entry:
                entry["item_id"] = entry.pop("practice_item_id")
                changed = True

            # 已有 item_id → 直接使用
            if "item_id" in entry:
                new_items.append(entry)
                stats["migrated"] += 1
                continue

            # 提取 item 名称
            item_name = entry.get("item", "")
            if not item_name:
                new_items.append(entry)
                continue

            # 泛化标签不创建 item_id，直接保留原样
            if item_name in SKIP_ITEMS:
                new_items.append(entry)
                continue

            matched_id, matched_name = fuzzy_match_item_id(item_name, [{"name": k, "item_id": v} for k, v in pi_map.items()])
            if matched_id:
                entry["item_id"] = matched_id
                new_items.append(entry)
                stats["migrated"] += 1
                changed = True  # 标记有改动
            elif item_name not in AUTO_CREATE_BLACKLIST:
                # 无法匹配 → 保留原样，不自动创建
                stats["unmatched_items"].append(f"assignment_id={assignment_id}: '{item_name}'")
                new_items.append(entry)  # 保留原样

        if changed or any("item_id" not in str(it) for it in items):
            if not dry_run:
                cursor.execute(
                    "UPDATE weekly_assignments SET items = ? WHERE id = ?",
                    (json.dumps(new_items, ensure_ascii=False), assignment_id)
                )

    if not dry_run:
        conn.commit()
    return stats


def migrate_daily_practices(conn: sqlite3.Connection, dry_run: bool = False) -> dict:
    """
    将 daily_practices.items JSON 中的条目补充 item_id。
    尝试 fuzzy match，匹配失败则 auto-create 新条目。
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, items FROM daily_practices")
    rows = cursor.fetchall()

    stats = {"total": 0, "migrated": 0, "auto_created": [], "unmatched": []}

    for row in rows:
        dp_id, dp_date, items_json = row["id"], row["date"], row["items"]
        if not items_json:
            continue

        try:
            items = json.loads(items_json)
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(items, list):
            continue

        new_items = []
        changed = False
        for entry in items:
            stats["total"] += 1
            if not isinstance(entry, dict):
                continue

            # 已有 item_id → 直接使用
            if "item_id" in entry or "practice_item_id" in entry:
                entry["item_id"] = entry.pop("practice_item_id", entry.get("item_id"))
                new_items.append(entry)
                stats["migrated"] += 1
                continue

            item_name = entry.get("item", "")
            if not item_name:
                continue

            # Fuzzy match
            cursor.execute("SELECT item_id, name FROM practice_items")
            pi_list = [{"name": r["name"], "item_id": r["item_id"]} for r in cursor.fetchall()]
            matched_id, matched_name = fuzzy_match_item_id(item_name, pi_list)

            if matched_id:
                entry["item_id"] = matched_id
                new_items.append(entry)
                stats["migrated"] += 1
                changed = True
            elif item_name not in AUTO_CREATE_BLACKLIST:
                # Auto-create 新条目（黑名单条目除外）
                if not dry_run:
                    cursor.execute(
                        "INSERT INTO practice_items (name, category_id, sort_order) VALUES (?, NULL, 0)",
                        (item_name,)
                    )
                    new_item_id = cursor.lastrowid
                    conn.commit()
                else:
                    new_item_id = 99999  # 占位
                entry["item_id"] = new_item_id
                new_items.append(entry)
                stats["auto_created"].append(item_name)
                stats["migrated"] += 1
                changed = True
            else:
                # 黑名单条目（病假等状态），不创建 item_id
                new_items.append(entry)

        # 只在真正有改动时更新（new_items 中有新增 item_id 的条目）
        needs_update = any("item_id" in it for it in new_items) and any("item_id" not in it for it in items)
        if not dry_run and (changed or needs_update):
            cursor.execute(
                "UPDATE daily_practices SET items = ? WHERE id = ?",
                (json.dumps(new_items, ensure_ascii=False), dp_id)
            )

    if not dry_run:
        conn.commit()
    return stats


# ─── 主入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="迁移 practice_items.id → item_id")
    parser.add_argument("--dry-run", action="store_true", help="只打印统计，不写入数据库")
    parser.add_argument("--backup", action="store_true", help="执行前先备份到 data/backups/")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"错误：数据库不存在 {DB_PATH}")
        sys.exit(1)

    # 备份
    if args.backup and not args.dry_run:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"dizi_pre_item_id_rename_{ts}.db"
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ 备份已保存: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}开始迁移...")
    print(f"  数据库: {DB_PATH}")
    print()

    # Step 1: 检测 practice_items 表结构，已迁移则跳过
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(practice_items)")
    pi_cols = [row[1] for row in cursor.fetchall()]

    if 'id' in pi_cols:
        print("1. 重建 practice_items 表 (id → item_id)...")
        try:
            stats1 = migrate_practice_items(conn)
            print(f"   ✅ 迁移 {stats1['rows']} 条记录")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            conn.close()
            sys.exit(1)
    else:
        print("1. practice_items 表已迁移（item_id 列已存在），跳过。")

    # Step 2: weekly_assignments JSON
    print("\n2. 迁移 weekly_assignments.items JSON...")
    try:
        stats2 = migrate_weekly_assignments(conn, dry_run=args.dry_run)
        print(f"   总条目: {stats2['total']}, 已含 item_id: {stats2['migrated']}")
        if stats2["unmatched_items"]:
            print(f"   ⚠️  无法匹配的条目 ({len(stats2['unmatched_items'])}):")
            for u in stats2["unmatched_items"][:10]:
                print(f"      - {u}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        conn.close()
        sys.exit(1)

    # Step 3: daily_practices JSON
    print("\n3. 迁移 daily_practices.items JSON...")
    try:
        stats3 = migrate_daily_practices(conn, dry_run=args.dry_run)
        print(f"   总条目: {stats3['total']}, 已含 item_id: {stats3['migrated']}")
        if stats3["auto_created"]:
            print(f"   🆕 自动创建的新 practice_items ({len(stats3['auto_created'])}):")
            for name in stats3["auto_created"][:10]:
                print(f"      - {name}")
        if stats3["unmatched"]:
            print(f"   ⚠️  无法匹配: {stats3['unmatched']}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        conn.close()
        sys.exit(1)

    # Step 4: daily_practices 添加 practiced 字段
    print("\n4. daily_practices 添加 practiced 字段...")
    try:
        cursor.execute("PRAGMA table_info(daily_practices)")
        dp_cols = [row[1] for row in cursor.fetchall()]
        if 'practiced' not in dp_cols:
            if not args.dry_run:
                cursor.execute("ALTER TABLE daily_practices ADD COLUMN practiced TEXT NOT NULL DEFAULT 'Y'")
                conn.commit()
                # 回填：total_minutes=0 且 item 为病假类 → 'N'
                SKIP_ITEMS_DP = {"病假", "休息", "未练", "请假", "早课", "晚课", "补课"}
                cursor.execute("SELECT id, items, total_minutes FROM daily_practices")
                for row in cursor.fetchall():
                    dp_id, items_json, total = row["id"], row["items"], row["total_minutes"]
                    if total == 0 and items_json:
                        try:
                            items = json.loads(items_json)
                            names = {it.get("item", "") for it in items}
                            if names <= SKIP_ITEMS_DP or names == {"病假"}:
                                cursor.execute("UPDATE daily_practices SET practiced='N' WHERE id=?", (dp_id,))
                        except Exception:
                            pass
                conn.commit()
            print("   ✅ practiced 列已添加并回填")
        else:
            print("   ⏭  practiced 列已存在，跳过")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        conn.close()
        sys.exit(1)

    conn.close()

    if args.dry_run:
        print("\n[DRY RUN] 以上为预览，实际未写入数据库。")
        print("         确认无误后，去掉 --dry-run 参数重新执行。")
    else:
        print("\n✅ 迁移完成！")
        print("   python3.14 -m pytest tests/ -v")
        print("   curl http://localhost:8765/prepare")


if __name__ == "__main__":
    main()
