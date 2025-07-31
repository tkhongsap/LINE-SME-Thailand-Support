#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime, timedelta

# Connect to database
conn = sqlite3.connect('instance/linebot.db')
cursor = conn.cursor()

# Get recent system logs
print("=== Recent System Logs ===")
cursor.execute("""
    SELECT created_at, level, message, error_trace 
    FROM system_logs 
    WHERE created_at > datetime('now', '-5 minutes')
    ORDER BY created_at DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row[0]} [{row[1]}] {row[2]}")
    if row[3]:
        print(f"  Trace: {row[3][:200]}...")

# Get recent webhook events
print("\n=== Recent Webhook Events ===")
cursor.execute("""
    SELECT created_at, event_type, user_id, processed, processing_time, error_message
    FROM webhook_events
    WHERE created_at > datetime('now', '-5 minutes')
    ORDER BY created_at DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row[0]} Type: {row[1]}, User: {row[2]}, Processed: {row[3]}, Time: {row[4]}ms")
    if row[5]:
        print(f"  Error: {row[5]}")

# Get recent conversations
print("\n=== Recent Conversations ===")
cursor.execute("""
    SELECT created_at, user_id, user_name, message_type, user_message, bot_response
    FROM conversations
    WHERE created_at > datetime('now', '-5 minutes')
    ORDER BY created_at DESC
    LIMIT 5
""")

for row in cursor.fetchall():
    print(f"{row[0]} User: {row[2]}, Type: {row[3]}")
    print(f"  User: {row[4]}")
    print(f"  Bot: {row[5]}")

conn.close()