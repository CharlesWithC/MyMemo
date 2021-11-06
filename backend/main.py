# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os, sys
if not os.path.exists("./database.db"):
    print("Database not found! If this is the first time you run this script, run firstuse.py first!")
    sys.exit(0)

import time
import json
import threading
import sqlite3

from app import app, config
import sessions
import api

def PendingAccountDeletion():
    conn = sqlite3.connect("database.db", check_same_thread=False)
    cur = conn.cursor()
    sscur = sessions.conn.cursor()
    while 1:
        sscur.execute(f"SELECT userId FROM PendingAccountDeletion WHERE deletionTime <= {int(time.time())}")
        d = sscur.fetchall()
        for dd in d:
            userId = dd[0]

            sessions.deleteData(userId)

            cur.execute(f"UPDATE UserInfo SET username = '@deleted' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {uid}")

            conn.commit()

        time.sleep(3600)

threading.Thread(target = PendingAccountDeletion).start()
if __name__ == "__main__":
    app.run(config.server_ip, config.server_port)