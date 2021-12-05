# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os, sys
from app import app, config
from db import newconn

import time
import json
import threading

import sessions
import functions
import api

def PendingAccountDeletion():
    while 1:
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT userId FROM PendingAccountDeletion WHERE deletionTime <= {int(time.time())}")
        d = cur.fetchall()
        for dd in d:
            userId = dd[0]

            sessions.deleteData(userId)

            cur.execute(f"UPDATE UserInfo SET username = '{encode('@deleted')}' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {uid}")

            conn.commit()
        

        time.sleep(3600)

threading.Thread(target = PendingAccountDeletion).start()
if __name__ == "__main__":
    app.run(config.server_ip, config.server_port)