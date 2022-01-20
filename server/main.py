#!/usr/bin/python3

# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os, sys
import uvicorn
from app import app, config
from db import newconn

from multiprocessing import Process
import time

import sessions
import functions
import api

class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
    def __del__(self):
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        self.file.close()
    def write(self, data):
        if "/api/admin/log" in data and "200 OK" in data or "NOLOG" in data:
            return
        self.stdout.write(data)
        self.file.write(data)
    def flush(self):
        self.file.flush()
    def isatty(self):
        return True

sys.stdout = Tee(config.log_file, "a")
sys.stderr = Tee(config.log_file, "a")

def PendingAccountDeletion():
    while 1:
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"SELECT userId FROM PendingAccountDeletion WHERE deletionTime <= {int(time.time())}")
        d = cur.fetchall()
        for dd in d:
            userId = dd[0]

            sessions.deleteData(userId)

            cur.execute(f"UPDATE UserInfo SET username = '{encode('@deleted')}' WHERE userId = {userId}")
            cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {userId}")
            cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {userId}")

            conn.commit()

        time.sleep(3600)

def PendingEmailVerificationDeletion():
    while 1:
        conn = newconn()
        cur = conn.cursor()

        cur.execute(f"DELETE FROM UserPending WHERE expire < {int(time.time())}")
        cur.execute(f"DELETE FROM EmailVerification WHERE expire < {int(time.time())}")
        cur.execute(f"DELETE FROM EmailHistory WHERE updateTS < {int(time.time())}")

        conn.commit()

        time.sleep(1200)

if __name__ == "__main__":
    padProc = Process(target = PendingAccountDeletion, daemon=True)
    padProc.start()
    pevdProc = Process(target = PendingEmailVerificationDeletion, daemon=True)
    pevdProc.start()

    print("My Memo v5.6.18 by Charles")
    time.sleep(5)
    uvicorn.run("app:app", host = config.server_ip, port = config.server_port)