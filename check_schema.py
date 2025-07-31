#!/usr/bin/env python3
import sqlite3

# Connect to database
conn = sqlite3.connect('instance/linebot.db')
cursor = conn.cursor()

# Get schema for each table
tables = ['conversation', 'system_log', 'webhook_event']

for table in tables:
    print(f"\n=== {table} schema ===")
    cursor.execute(f"PRAGMA table_info({table})")
    for col in cursor.fetchall():
        print(f"  {col[1]} ({col[2]})")

conn.close()