# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os, sys
import time
import json
import threading
import sqlite3

from app import app, config
import sessions
import api


if not os.path.exists("./database.db"):
    print("Database not found! If this is the first time you run this script, run firstuse.py first!")
    sys.exit(0)

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
            cur.execute(f"DELETE FROM WordList WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBook WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBookShare WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordMemorized WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBookProgress WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeRecord WHERE userId = {uid}")
            cur.execute(f"DELETE FROM StatusUpdate WHERE userId = {uid}")
            cur.execute(f"DELETE FROM GroupMember WHERE userId = {uid}")
            cur.execute(f"DELETE FROM GroupSync WHERE userId = {uid}")
            cur.execute(f"DELETE FROM GroupBind WHERE userId = {uid}")

            conn.commit()

        time.sleep(3600)

def ClearCache():
    while 1:
        recoverAccount = []
        duplicate = []
        os.system("rm -f /tmp/WordMemoCache/*")
        time.sleep(3600) # clear each hour

threading.Thread(target = PendingAccountDeletion).start()
threading.Thread(target = ClearCache).start()

app.run(config.server_ip, config.server_port)