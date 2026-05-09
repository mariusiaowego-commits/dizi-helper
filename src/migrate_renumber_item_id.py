#!/usr/bin/env python3.14
"""将 practice_items.item_id 从当前值重写为 1001~ 四位序号，同时更新所有 JSON 引用。"""

import sqlite3, json, shutil, datetime, sys
from pathlib import Path

DB_PATH = Path("data/dizi.db")
BACKUP_SUFFIX = f"itemid_renumber_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def log(msg):
    print(msg, flush=True)

def migrate():
    # 1. 备份
    backup = DB_PATH.parent / f"{DB_PATH.stem}_backup_{BACKUP_SUFFIX}{DB_PATH.suffix}"
    shutil.copy2(DB_PATH, backup)
    log(f"✅ 备份: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 2. 收集所有唯一 item_id（在 JSON 中出现的）
    log("\n[1/5] 收集所有 item_id...")
    all_ids = set()
    for table, col in [("weekly_assignments", "items"), ("daily_practices", "items")]:
        cur = conn.execute(f"SELECT {col} FROM {table}")
        for row in cur:
            if row[col]:
                items = json.loads(row[col]) if isinstance(row[col], str) else row[col]
                for it in items:
                    if "item_id" in it and it["item_id"]:
                        all_ids.add(it["item_id"])

    log(f"   JSON 中出现过的 item_id 共 {len(all_ids)} 个: {sorted(all_ids)}")

    # 3. 建立新旧映射（按原值升序，分配新序号 1001+）
    old_to_new = {}
    for new_id, old_id in enumerate(sorted(all_ids), start=1001):
        old_to_new[old_id] = new_id
    log(f"\n[2/5] 映射: {old_to_new}")

    # 4. 重写 practice_items.item_id
    log("\n[3/5] 重写 practice_items.item_id...")
    # 读取所有记录
    cur = conn.execute("SELECT rowid, item_id, name FROM practice_items ORDER BY item_id")
    rows = {row[1]: (row[0], row[2]) for row in cur}

    updated_items = {}
    for old_id, new_id in old_to_new.items():
        if old_id in rows:
            rowid, name = rows[old_id]
            conn.execute("UPDATE practice_items SET item_id=? WHERE rowid=?", (new_id, rowid))
            updated_items[new_id] = name
            log(f"   {old_id} → {new_id}: {name}")

    # 处理不在 JSON 中出现的 item_id（分配更高序号）
    used_new_ids = set(old_to_new.values())
    next_id = max(used_new_ids) + 1 if used_new_ids else 1001
    for old_id, (rowid, name) in rows.items():
        if old_id not in old_to_new:
            conn.execute("UPDATE practice_items SET item_id=? WHERE rowid=?", (next_id, rowid))
            log(f"   {old_id} → {next_id}: {name} (不在JSON中，分配新号)")
            old_to_new[old_id] = next_id
            next_id += 1

    conn.commit()

    # 5. 更新所有 JSON 中的 item_id
    log("\n[4/5] 更新 JSON 中的 item_id 引用...")
    total_updated = 0
    for table, col in [("weekly_assignments", "items"), ("daily_practices", "items")]:
        cur = conn.execute(f"SELECT rowid, {col} FROM {table}")
        for row in cur:
            raw = row[1]
            if not raw:
                continue
            items = json.loads(raw) if isinstance(raw, str) else raw
            changed = False
            for it in items:
                if it.get("item_id") and it["item_id"] in old_to_new:
                    it["item_id"] = old_to_new[it["item_id"]]
                    changed = True
            if changed:
                conn.execute(
                    f"UPDATE {table} SET {col}=? WHERE rowid=?",
                    (json.dumps(items, ensure_ascii=False), row[0])
                )
                total_updated += 1

    conn.commit()
    log(f"   更新了 {total_updated} 条 JSON 记录")

    # 6. 验证
    log("\n[5/5] 验证...")
    cur = conn.execute("SELECT MIN(item_id), MAX(item_id), COUNT(*) FROM practice_items")
    row = cur.fetchone()
    log(f"   practice_items: min={row[0]}, max={row[1]}, count={row[2]}")

    # 检查 JSON 残留旧 item_id
    orphan_count = 0
    for table, col in [("weekly_assignments", "items"), ("daily_practices", "items")]:
        cur = conn.execute(f"SELECT rowid, {col} FROM {table}")
        for row in cur:
            if not row[1]:
                continue
            items = json.loads(row[1]) if isinstance(row[1], str) else row[1]
            for it in items:
                if "item_id" in it and it["item_id"] and it["item_id"] not in old_to_new.values():
                    orphan_count += 1
                    log(f"   ⚠️  {table} rowid={row[0]}: 残留旧 item_id={it['item_id']} in {it}")

    if orphan_count == 0:
        log("   ✅ 无残留旧 item_id")

    conn.close()
    log("\n✅ 完成！四位 item_id 范围: 1001~")

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    if dry:
        log("DRY RUN - 不写入数据库")
    migrate()
