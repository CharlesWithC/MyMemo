# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os, time, uuid
import sqlite3

# Unexpected errors often happen
# So automatically restart the program when there are 5 errors
errcnt = 0

db_exists = os.path.exists("sessions.db")
conn = sqlite3.connect("sessions.db", check_same_thread=False)
cur = conn.cursor()
if not db_exists:
    cur.execute(f"CREATE TABLE ActiveUserLogin (userId INT, token CHAR(46), loginTime INT, expireTime INT)")
    # Active user login data
    # Remove data when expired / logged out
    # Token = 9-digit-userId + '-' + uuid.uuid(4)

    cur.execute(f"CREATE TABLE UserSessionHistory (userId INT, loginTime INT, logoutTime INT, expire INT)")
    # User Session History, updated when user logs out
    # If user logged out manually, then logout time is his/her logout time and "expire" will be set to 0
    # If the token expired, then logout time is the expireTime and "expire" will be set to 1
    # When the user changes his/her password, all of the sessions will be logged out, and expire will be set to 2

    cur.execute(f"CREATE TABLE PendingAccountDeletion (userId INT, deletionTime INT)")

    cur.execute(f"CREATE TABLE PasswordTrial (userId INT, count INT, lastts INT)")


def validateToken(userId, token):
    try:
        cur = conn.cursor()
        if not token.replace("-","").isalnum():
            return False

        cur.execute(f"SELECT loginTime, expireTime FROM ActiveUserLogin WHERE userId = {userId} AND token = '{token}'")
        d = cur.fetchall()
        if len(d) == 0:
            return False

        loginTime = d[0][0]
        expireTime = d[0][1]

        if expireTime <= int(time.time()):
            cur.execute(f"DELETE FROM ActiveUserLogin WHERE userId = {userId} AND token = '{token}'")
            cur.execute(f"INSERT INTO UserSessionHistory VALUES ({userId}, {loginTime}, {expireTime}, 1)")
            conn.commit()
            return False
        
        else:
            return True

    except:
        global errcnt
        errcnt += 1

def login(userId):
    try:
        token = str(userId).zfill(9) + "-" + str(uuid.uuid4())
        loginTime = int(time.time())
        expireTime = loginTime + 21600 # 6 hours

        cur.execute(f"INSERT INTO ActiveUserLogin VALUES ({userId}, '{token}', {loginTime}, {expireTime})")
        conn.commit()

        return token
    
    except:
        global errcnt
        errcnt += 1

def logout(userId, token):
    try:
        if not validateToken(userId, token):
            return True
        
        cur.execute(f"SELECT loginTime FROM ActiveUserLogin WHERE userId = {userId} AND token = '{token}'")
        d = cur.fetchall()
        loginTime = d[0][0]
        cur.execute(f"DELETE FROM ActiveUserLogin WHERE userId = {userId} AND token = '{token}'")
        cur.execute(f"INSERT INTO UserSessionHistory VALUES ({userId}, {loginTime}, {int(time.time())}, 0)")
        conn.commit()

        return True

    except:
        global errcnt
        errcnt += 1

def logoutAll(userId):
    try: 
        cur.execute(f"SELECT * FROM ActiveUserLogin WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            cur.execute(f"INSERT INTO UserSessionHistory VALUES ({userId}, {dd[2]}, {int(time.time())}, 2)")
        cur.execute(f"DELETE FROM ActiveUserLogin WHERE userId = {userId}")
        conn.commit()

        return True
        
    except:
        global errcnt
        errcnt += 1

def getPasswordTrialCount(userId):
    try:
        cur.execute(f"SELECT count, lastts FROM PasswordTrial WHERE userId = {userId}")
        t = cur.fetchall()
        if len(t) == 0:
            return (0, 0)
        else:
            return (t[0][0], t[0][1])

    except:
        global errcnt
        errcnt += 1

def updatePasswordTrialCount(userId, to, ts):
    try:
        cur.execute(f"SELECT count FROM PasswordTrial WHERE userId = {userId}")
        t = cur.fetchall()
        if len(t) == 0:
            if to == 0:
                return
            cur.execute(f"INSERT INTO PasswordTrial VALUES ({userId}, {to}, {ts})")
            conn.commit()
        else:
            if to == 0:
                cur.execute(f"DELETE FROM PasswordTrial WHERE userId = {userId}")
                conn.commit()
            else:
                cur.execute(f"UPDATE PasswordTrial SET count = {to} WHERE userId = {userId}")
                cur.execute(f"UPDATE PasswordTrial SET lastts = {ts} WHERE userId = {userId}")
                conn.commit()

    except:
        global errcnt
        errcnt += 1
    

def deleteData(userId):
    try:
        cur.execute(f"DELETE FROM ActiveUserLogin WHERE userId = {userId}")
        cur.execute(f"DELETE FROM UserSessionHistory WHERE userId = {userId}")
        cur.execute(f"DELETE FROM PendingAccountDeletion WHERE userId = {userId}")
        
    except:
        global errcnt
        errcnt += 1

def markDeletion(userId):
    try:
        cur.execute(f"INSERT INTO PendingAccountDeletion VALUES ({userId}, {int(time.time()+86401*14)})")
        conn.commit()
        
    except:
        global errcnt
        errcnt += 1

def checkDeletionMark(userId):
    try:
        cur.execute(f"SELECT * FROM PendingAccountDeletion WHERE userId = {userId}")
        if len(cur.fetchall()) > 0:
            return True
        else:
            return False
        
    except:
        global errcnt
        errcnt += 1

def removeDeletionMark(userId):
    try:
        cur.execute(f"DELETE FROM PendingAccountDeletion WHERE userId = {userId}")
        conn.commit()
        
    except:
        global errcnt
        errcnt += 1

def DeleteAccountNow(userId):
    try:
        cur = conn.cursor()

        cur.execute(f"SELECT userId FROM PendingAccountDeletion WHERE userId = {userId}")
        if len(cur.fetchall()) == 0:
            return -1
            
        deleteData(userId)
        conn.commit()
        
        return 0

    except:
        global errcnt
        errcnt += 1

def CheckDeletionMark(userId):
    try:
        cur = conn.cursor()

        cur.execute(f"SELECT userId FROM PendingAccountDeletion WHERE userId = {userId}")
        if len(cur.fetchall()) != 0:
            return 1
        
        return 0

    except:
        global errcnt
        errcnt += 1

def CountDeletionMark():
    try:
        cur = conn.cursor()

        cur.execute(f"SELECT COUNT(*) FROM PendingAccountDeletion")
        d = cur.fetchall()
        if len(d) == 0:
            return 0
        
        return d[0][0]

    except:
        global errcnt
        errcnt += 1