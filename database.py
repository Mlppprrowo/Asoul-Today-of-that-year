import sqlite3

conn = sqlite3.connect('dynamic.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS dynamic (
    id TEXT PRIMARY KEY,
    user TEXT,
    pub_time INTEGER,
    content TEXT,
    img_urls TEXT
)
""")
conn.commit()

def insert_dynamic(id, user, pub_time, content, img_urls=None):
    cursor.execute(
        "INSERT OR IGNORE INTO dynamic (id, user, pub_time, content, img_urls) VALUES (?,?,?,?,?)",
        (id, user, pub_time, content, img_urls)
    )
    conn.commit()

# 判断数据库里 有没有这条动态
def exists(dynamic_id):
    cursor.execute("SELECT 1 FROM dynamic WHERE id=?", (dynamic_id,))
    return cursor.fetchone() is not None
