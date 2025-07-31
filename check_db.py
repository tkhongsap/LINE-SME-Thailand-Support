#!/usr/bin/env python3
import sqlite3

# Connect to database
conn = sqlite3.connect('instance/linebot.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check conversations table
print("\nRecent conversations:")
cursor.execute("SELECT * FROM conversation ORDER BY created_at DESC LIMIT 5")
cols = [description[0] for description in cursor.description]
print(f"Columns: {cols}")

for row in cursor.fetchall():
    print(row)

conn.close()