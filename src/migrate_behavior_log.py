#!/usr/bin/env python3
"""Migration: add behavior_log column to daily_practices table."""
import sqlite3, sys, os, json

DB_PATH = '/Users/mt16/dev/dizical/data/dizi.db'

def migrate(dry_run=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(daily_practices)")
    cols = [row[1] for row in cursor.fetchall()]

    if 'behavior_log' in cols:
        print("✓ behavior_log column already exists, nothing to do.")
        conn.close()
        return

    print("Adding behavior_log column to daily_practices...")
    if not dry_run:
        cursor.execute("ALTER TABLE daily_practices ADD COLUMN behavior_log TEXT NOT NULL DEFAULT '[]'")
        conn.commit()
    print("✓ Done.")
    conn.close()

if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    if dry:
        print("[dry-run mode]")
    migrate(dry_run=dry)
