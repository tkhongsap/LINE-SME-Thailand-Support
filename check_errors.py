#!/usr/bin/env python3
import sqlite3
from datetime import datetime

# Connect to database
conn = sqlite3.connect('instance/linebot.db')
cursor = conn.cursor()

# Get recent system logs
print("=== Recent System Logs (Errors) ===")
cursor.execute("""
    SELECT created_at, level, message, error_details 
    FROM system_log 
    WHERE level IN ('ERROR', 'WARNING') 
    AND created_at > datetime('now', '-15 minutes')
    ORDER BY created_at DESC
    LIMIT 20
""")

for row in cursor.fetchall():
    print(f"{row[0]} [{row[1]}] {row[2]}")
    if row[3]:
        print(f"  Details: {row[3][:300]}...")

# Get recent webhook events with errors
print("\n=== Recent Webhook Events with Errors ===")
cursor.execute("""
    SELECT created_at, event_type, user_id, processed, processing_time, error_message
    FROM webhook_event
    WHERE error_message IS NOT NULL
    OR processed = 0
    ORDER BY created_at DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row[0]} Type: {row[1]}, User: {row[2]}, Processed: {row[3]}, Time: {row[4]}ms")
    if row[5]:
        print(f"  Error: {row[5]}")

# Check if any conversations were saved
print("\n=== Recent Conversations ===")
cursor.execute("""
    SELECT COUNT(*) FROM conversation WHERE created_at > datetime('now', '-15 minutes')
""")
count = cursor.fetchone()[0]
print(f"Conversations in last 15 minutes: {count}")

conn.close()