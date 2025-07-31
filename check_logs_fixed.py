#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('instance/linebot.db')
cursor = conn.cursor()

# Get recent system logs
print("=== Recent System Logs ===")
cursor.execute("""
    SELECT created_at, level, message, error_trace 
    FROM system_log 
    WHERE created_at > datetime('now', '-10 minutes')
    ORDER BY created_at DESC
    LIMIT 20
""")

for row in cursor.fetchall():
    print(f"{row[0]} [{row[1]}] {row[2]}")
    if row[3]:
        print(f"  Trace: {row[3][:200]}...")

# Get recent webhook events
print("\n=== Recent Webhook Events ===")
cursor.execute("""
    SELECT created_at, event_type, user_id, processed, processing_time, error_message
    FROM webhook_event
    WHERE created_at > datetime('now', '-10 minutes')
    ORDER BY created_at DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row[0]} Type: {row[1]}, User: {row[2]}, Processed: {row[3]}, Time: {row[4]}ms")
    if row[5]:
        print(f"  Error: {row[5]}")

conn.close()