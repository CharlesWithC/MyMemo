# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os, sys
from app import app, config
import db

import time
import json
import threading

import MySQLdb
import sqlite3

import sessions
import functions
import api

functions.updateconn()
sessions.updateconn()

def PendingAccountDeletion():
    conn = None
    if config.database == "mysql":
        conn = MySQLdb.connect(host = app.config["MYSQL_HOST"], user = app.config["MYSQL_USER"], \
            passwd = app.config["MYSQL_PASSWORD"], db = app.config["MYSQL_DB"])
    else:
        conn = sqlite3.connect("database.db", check_same_thread = False)
    cur = conn.cursor()
    while 1:
        cur.execute(f"SELECT userId FROM PendingAccountDeletion WHERE deletionTime <= {int(time.time())}")
        d = cur.fetchall()
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