import sqlite3
import os

db_exists = os.path.exists("/tmp/mymemo_temp.db")
conn = sqlite3.connect("/tmp/mymemo_temp.db", check_same_thread=False)
cur = conn.cursor()
if not db_exists:
    cur.execute(f"CREATE TABLE DataDownloadToken (userId INT, exportType VARCHAR(10), ts INT, token VARCHAR(32))")
    cur.execute(f"CREATE TABLE RequestRecoverAccount (userId INT)")
    conn.commit()