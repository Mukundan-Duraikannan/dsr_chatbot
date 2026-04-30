import sqlite3

conn = sqlite3.connect("test.db")
cursor = conn.cursor()

cursor.execute("UPDATE daily_logs SET log_date = '2026-04-28' WHERE employee_id = 4")

conn.commit()
conn.close()

print("Updated successfully")