import os, time, uuid
import sqlite3

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


def validateToken(userId, token):
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

def login(userId):
    token = str(userId).zfill(9) + "-" + str(uuid.uuid4())
    loginTime = int(time.time())
    expireTime = loginTime + 7200 # 2 hours

    cur.execute(f"INSERT INTO ActiveUserLogin VALUES ({userId}, '{token}', {loginTime}, {expireTime})")
    conn.commit()

    return token

def logout(userId, token):
    if not validateToken(userId, token):
        return True
    
    cur.execute(f"SELECT loginTime FROM ActiveUserLogin WHERE userId = {userId} AND token = '{token}'")
    d = cur.fetchall()
    loginTime = d[0][0]
    cur.execute(f"DELETE FROM ActiveUserLogin WHERE userId = {userId} AND token = '{token}'")
    cur.execute(f"INSERT INTO UserSessionHistory VALUES ({userId}, {loginTime}, {int(time.time())}, 0)")
    conn.commit()

    return True

def logoutAll(userId):    
    cur.execute(f"SELECT * FROM ActiveUserLogin WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        cur.execute(f"INSERT INTO UserSessionHistory VALUES ({userId}, {dd[2]}, {int(time.time())}, 2)")
    cur.execute(f"DELETE FROM ActiveUserLogin WHERE userId = {userId}")
    conn.commit()

    return True

def deleteData(userId):
    cur.execute(f"DELETE FROM ActiveUserLogin WHERE userId = {userId}")
    cur.execute(f"DELETE FROM UserSessionHistory WHERE userId = {userId}")
    cur.execute(f"DELETE FROM PendingAccountDeletion WHERE userId = {userId}")

def markDeletion(userId):
    cur.execute(f"INSERT INTO PendingAccountDeletion VALUES ({userId}, {int(time.time()+86401*14)})")
    conn.commit()

def checkDeletionMark(userId):
    cur.execute(f"SELECT * FROM PendingAccountDeletion WHERE userId = {userId}")
    if len(cur.fetchall()) > 0:
        return True
    else:
        return False

def removeDeletionMark(userId):
    cur.execute(f"DELETE FROM PendingAccountDeletion WHERE userId = {userId}")
    conn.commit()
    
def PendingAccountDeletion():
    cur = conn.cursor()
    while 1:
        cur.execute(f"SELECT userId FROM PendingAccountDeletion WHERE deletionTime <= {int(time.time())}")
        d = cur.fetchall()
        for dd in d:
            userId = dd[0]
            cur.execute(f"UPDATE UserInfo SET username = '@deleted' WHERE userId = {userId}")
            cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {userId}")
            cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {userId}")
            
            deleteData(userId)

            cur.execute(f"DELETE FROM WordList WHERE userId = {userId}")
            cur.execute(f"DELETE FROM ChallengeData WHERE userId = {userId}")
            cur.execute(f"DELETE FROM ChallengeRecord WHERE userId = {userId}")
            cur.execute(f"DELETE FROM DeletedWordList WHERE userId = {userId}")
            cur.execute(f"DELETE FROM StatusUpdate WHERE userId = {userId}")

            conn.commit()

        time.sleep(3600)