import sqlite3

conn = sqlite3.connect('bti.db')
cursor = conn.cursor()
cursor.execute("SELECT id, name, image_url FROM team_members")
members = cursor.fetchall()
print("Поточні дані команди:")
for id, name, image_url in members:
    print(f"ID {id}: {name} -> {image_url}")
conn.close()
