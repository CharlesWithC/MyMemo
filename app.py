# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import Flask, render_template, request, abort, send_file
import os, sys, datetime, time, threading
import random, uuid
import base64, bcrypt
import json
import validators
import sqlite3
import pandas as pd

import sessions

StatusTextToStatus = {"Default": 1, "Tagged": 2, "Removed": 3}
StatusToStatusText = {1: "Default", 2: "Tagged", 3: "Removed"}
wordCnt = 0

def hashpwd(password):
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt(12)).decode()

def checkpwd(password, hsh):
    return bcrypt.checkpw(password.encode(),hsh.encode())

st="abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def gencode(length = 6):
    ret = ""
    for _ in range(length):
        ret += st[random.randint(0,len(st)-1)]
    return ret

db_exists = os.path.exists("database.db")
conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()
if not db_exists:
    cur.execute(f"CREATE TABLE UserInfo (userId INT, username VARCHAR(64), email VARCHAR(128), password VARCHAR(256), inviter INT, inviteCode CHAR(5))")
    # Allow only inviting registration mode to prevent abuse

    # User should be allowed to delete their accounts
    # When a user request to delete his account, his account will be marked as "Pending for deletion",
    # and will be deleted in 14 days. 
    # During the 14 days, user will be allowed to recover the account. (Like Discord)
    # After the 14 days, all of the user's data will be wiped, including UserInfo, WordList, ChallengeData etc
    # But his/her userId will persist forever, while it represents an empty account named "Deleted Account"

    defaultpwd = hashpwd("123456")
    cur.execute(f"INSERT INTO UserInfo VALUES (0,'default','None','{defaultpwd}',-1,'{gencode()}')")
    # Default user system's password is 123456

    cur.execute(f"CREATE TABLE AdminList (userId INT)")
    # Currently this admin list can only be edited from backend using database operations

    cur.execute(f"CREATE TABLE WordList (userId INT, wordId INT, word VARCHAR(1024), translation VARCHAR(1024), status INT)")
    # wordId is unique for each word, when the word is removed, its wordId will refer to null
    # EXAMPLE: WordBook 1 has wordId 1,2 and WordBook 2 has wordId 3
    # word and translation are encoded with base64 to prevent datalose
    # status is a status code while 1 refers to Default, 2 refers to Tagged and 3 refers to removed

    cur.execute(f"CREATE TABLE WordBook (userId INT, wordBookId INT, name VARCHAR(1024))")
    cur.execute(f"CREATE TABLE WordBookData (userId INT, wordBookId INT, wordId INT)")
    # When a new word is added, it belongs to no word book
    # A word can belong to many word books

    cur.execute(f"CREATE TABLE ChallengeData (userId INT, wordId INT, nextChallenge INT, lastChallenge INT)")
    # Challenge Data is a table that tells when to display the word next time
    # nextChallenge and lastChallenge are both timestamps
    # When a new word is added, there should be a record of it with nextChallenge = 0, lastChallenge = -1
    # When the user says that he/she memorized the word, then nextChallenge will be extended to a longer time based on forgetting curve
    # When the user says that he/she forgot the word, then nextChallenge will be set to 1 hour later

    # In challenge mode, the words to display contains all the words in the wordlist
    # The percentage of showing a word is:
    # 35%: Words that are tagged
    # 30%: NextChallenge != 0 && NextChallenge <= int(time.time())
    # 30%: NextChallenge == 0
    # 5%: Words that are deleted (to make sure the user still remember it)

    cur.execute(f"CREATE TABLE ChallengeRecord (userId INT, wordId INT, memorized INT, timestamp INT)")
    # This is the record of historical challenges

    cur.execute(f"CREATE TABLE DeletedWordList (userId INT, wordId INT, word VARCHAR(1024), translation VARCHAR(1024), status INT, deleteTimestamp INT)")
    # This is the list of all permanently deleted words (which will never be shown on user side)

    cur.execute(f"CREATE TABLE StatusUpdate (userId INT, wordId INT, wordUpdateId INT, updateTo INT, timestamp INT)")
    # wordUpdateId is the Id for the specific word
    # updateTo is the status the word is updated to
    # NOTE: When a new word is added, there should be a StatusUpdate record, with wordUpdateId = 0 and updateTo = 0

    conn.commit()
del cur

def encode(s):
    return base64.b64encode(s.encode()).decode()

def decode(s):
    return base64.b64decode(s.encode()).decode()

def getWordCount(userId):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
    return cur.fetchall()[0][0]

def updateWordStatus(userId, wordId, status):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    wordUpdateId = 0
    if len(d) != 0:
        wordUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({userId},{wordId},{wordUpdateId},{status},{int(time.time())})")

def validateToken(userId, token):
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0 or d[0][0] == "@deleted":
        return False
    
    return sessions.validateToken(userId, token)


app=Flask(__name__)

@app.route("/", methods = ['GET'])
def index():
    return render_template("index.html")

@app.route("/user", methods = ['GET'])
def userIndex():
    return render_template("user.html")

@app.route("/ping", methods = ['POST'])
def ping():
    msg = request.form["msg"]
    return json.dumps({"success": True, "msg": msg})





##########
# User API

@app.route("/api/register", methods = ['POST'])
def apiRegister():
    cur = conn.cursor()
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    invitationCode = request.form["invitationCode"]

    if username is None or email is None or password is None or invitationCode is None \
        or username.replace(" ","") == "" or email.replace(" ","") == "" or password.replace(" ","") == "" or invitationCode.replace(" ","") == "":
        return json.dumps({"success": False, "msg": "All the fields must be filled!"})
    if not username.replace("_","").isalnum():
        return json.dumps({"success": False, "msg": "Username can only contain alphabets, digits and underscore!"})
    if validators.email(email) != True:
        return json.dumps({"success": False, "msg": "Invalid email!"})
    if not invitationCode.isalnum():
        return json.dumps({"success": False, "msg": "Invitation code can only contain alphabets and digits!"})

    cur.execute(f"SELECT username FROM UserInfo WHERE username = '{username}'")
    if len(cur.fetchall()) != 0:
        return json.dumps({"success": False, "msg": "Username already registered!"})

    password = hashpwd(password)
    
    cur.execute(f"SELECT userId FROM UserInfo WHERE inviteCode = '{invitationCode}'")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Invalid invitation code!"})
    inviter = d[0][0]
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {inviter}")
    if cur.fetchall()[0][0] == "@deleted":
        return json.dumps({"success": False, "msg": "Invalid invitation code!"})

    inviteCode = gencode()

    try:
        cur.execute(f"SELECT MAX(userId) FROM UserInfo")
        userId = cur.fetchall()[0][0] + 1
        cur.execute(f"INSERT INTO UserInfo VALUES ({userId}, '{username}', '{email}', '{encode(password)}', {inviter}, '{inviteCode}')")
        conn.commit()
    except:
        sessions.errcnt += 1

    return json.dumps({"success": True, "msg": "You are registered! Now you can login!"})

recoverAccount = []
@app.route("/api/login", methods = ['POST'])
def apiLogin():
    cur = conn.cursor()
    username = request.form["username"]
    password = request.form["password"]
    if not username.replace("_","").isalnum():
        return json.dumps({"success": False, "msg": "Username can only contain alphabets, digits and underscore!"})
    
    try:
        cur.execute(f"SELECT userId, password FROM UserInfo WHERE username = '{username}'")
        d = cur.fetchall()
        if len(d) == 0:
            return json.dumps({"success": False, "msg": "User does not exist!"})
        d = d[0]
    except:
        sessions.errcnt += 1
        
    if not checkpwd(password,decode(d[1])):
        return json.dumps({"success": False, "msg": "Invalid password!"})
    
    userId = d[0]

    if not userId in recoverAccount:
        if sessions.checkDeletionMark(userId):
            recoverAccount.append(userId)
            return json.dumps({"success": False, "msg": "Account marked for deletion, login again to recover it!"})
    else:
        recoverAccount.remove(userId)
        sessions.removeDeletionMark(userId)

    token = sessions.login(userId)

    isAdmin = False
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        isAdmin = True

    return json.dumps({"success": True, "userId": userId, "token": token, "isAdmin": isAdmin})

@app.route("/api/logout", methods = ['POST'])
def apiLogout():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        return json.dumps({"success": True})

    userId = int(request.form["userId"])
    token = request.form["token"]
    ret = sessions.logout(userId, token)

    return json.dumps({"success": ret})

@app.route("/api/deleteAccount", methods = ['POST'])
def apiDeleteAccount():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    password = request.form["password"]
    cur.execute(f"SELECT password FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    pwdhash = d[0][0]
    if not checkpwd(password,decode(pwdhash)):
        return json.dumps({"success": False, "msg": "Invalid password!"})
    
    sessions.markDeletion(userId)

    sessions.logout(userId, token)

    return json.dumps({"success": True})

@app.route("/api/validateToken", methods = ['POST'])
def apiValidateToken():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        return json.dumps({"validation": False})
    userId = int(request.form["userId"])
    token = request.form["token"]
    return json.dumps({"validation": validateToken(userId, token)})

@app.route("/api/getUserInfo", methods = ['POST'])
def apiGetUserInfo():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cur.execute(f"SELECT username, email, inviteCode, inviter FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()[0]

    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {d[3]}")
    inviter = cur.fetchall()[0][0]

    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
    cnt = cur.fetchall()[0][0]

    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId} AND status = 2")
    tagcnt = cur.fetchall()[0][0]

    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId} AND status = 3")
    delcnt = cur.fetchall()[0][0]

    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {userId}")
    chcnt = cur.fetchall()[0][0]

    return json.dumps({"username": d[0], "email": d[1], "invitationCode": d[2], "inviter": inviter, "cnt": cnt, "tagcnt": tagcnt, "delcnt": delcnt, "chcnt": chcnt})

@app.route("/api/changePassword", methods=['POST'])
def apiChangePassword():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    oldpwd = request.form["oldpwd"]
    newpwd = request.form["newpwd"]
    cfmpwd = request.form["cfmpwd"]
    
    cur.execute(f"SELECT password FROM UserInfo WHERE userId = {userId}")
    pwd = cur.fetchall()[0][0]
    if not checkpwd(oldpwd, decode(pwd)):
        return json.dumps({"success": False, "msg": "Incorrect old password!"})

    if newpwd != cfmpwd:
        return json.dumps({"success": False, "msg": "New password and confirm password mismatch!"})

    newhashed = hashpwd(newpwd)
    cur.execute(f"UPDATE UserInfo SET password = '{encode(newhashed)}' WHERE userId = {userId}")
    
    sessions.logoutAll(userId)

    return json.dumps({"success": True})





##########
# Admin API

@app.route("/api/admin/restart", methods = ['POST'])
def apiAdminRestart():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        abort(401)
    
    if os.path.exists("/tmp/WordMemoLastManualRestart"):
        lst = int(open("/tmp/WordMemoLastManualRestart","r").read())
        if int(time.time()) - lst <= 1800:
            return json.dumps({"success": False, "msg": "Only one restart in each 30 minutes is allowed!"})
    
    open("/tmp/WordMemoLastManualRestart","w").write(str(int(time.time())))

    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
    sys.exit(0)

# NOTE It's dangerous
# Make sure this route is protected by reverse proxy (nginx / apache) authentication
# Otherwise remove the route to prevent your server from being attacked
@app.route("/protected/restart", methods = ['GET'])
def nginxProtectedRestart():
    if os.path.exists("/tmp/WordMemoLastManualRestart"):
        lst = int(open("/tmp/WordMemoLastManualRestart","r").read())
        if int(time.time()) - lst <= 1800:
            return "Only one restart in each 30 minutes is allowed!"
    
    open("/tmp/WordMemoLastManualRestart","w").write(str(int(time.time())))

    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
    sys.exit(0)




##########
# Word API

@app.route("/api/getWordBookList", methods = ['POST'])
def apiGetWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []
    cur.execute(f"SELECT wordBookId, name FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        words = []
        cur.execute(f"SELECT wordId FROM WordBookData WHERE wordBookId = {dd[0]}")
        t = cur.fetchall()
        for tt in t:
            words.append(tt[0])
        ret.append({"wordBookId": dd[0], "name": decode(dd[1]), "words": words})
    
    return json.dumps(ret)

@app.route("/api/createWordBook", methods = ['POST'])
def apiCreateWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    name = request.form["name"]
    name = encode(name)

    wordBookId = 1
    cur.execute(f"SELECT MAX(wordBookId) FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and not d[0][0] is None:
        wordBookId = d[0][0] + 1
    
    cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")
    conn.commit()
    return json.dumps({"success": True})

@app.route("/api/deleteWordBook", methods = ['POST'])
def apiDeleteWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["wordBookId"])
    cur.execute(f"SELECT name FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})

    cur.execute(f"DELETE FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/addToWordBook", methods = ['POST'])
def apiAddToWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    words = json.loads(request.form["words"])
    wordBookId = int(request.form["wordBookId"])

    cur.execute(f"SELECT name FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})
    
    cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()

    cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    t = cur.fetchall()

    for wordId in words:
        if (wordId,) in d and not (wordId,) in t:
            cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/deleteFromWordBook", methods = ['POST'])
def apiDeleteFromWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    words = json.loads(request.form["words"])
    wordBookId = int(request.form["wordBookId"])

    cur.execute(f"SELECT name FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})
    
    cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()

    for wordId in words:
        if (wordId,) in d:
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId} AND wordId = {wordId}")
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/getWordList", methods = ['POST'])
def apiGetWordList():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []
    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        ret.append({"wordId": dd[0], "word": decode(dd[1]), "translation": decode(dd[2]), "status": dd[3]})
    
    return json.dumps(ret)

@app.route("/api/getWord", methods = ['POST'])
def apiGetWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordId = int(request.form["wordId"])
    
    cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()

    if len(d) == 0:
        abort(404)
    
    (word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    return json.dumps({"wordId": wordId, "word":word, "translation": translation, "status": status})

@app.route("/api/getWordId", methods = ['POST'])
def apiGetWordID():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    word = request.form["word"]
    cur.execute(f"SELECT wordId FROM WordList WHERE word = '{encode(word)}' AND userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0:
        wordId = d[0][0]
        # If there are multiple records, then return the first one
        # NOTE: The user should be warned when they try to insert multiple records with the same word
        return json.dumps({"wordId" : wordId})
    else:
        abort(404)

@app.route("/api/getWordStat", methods = ['POST'])
def apiGetWordStat():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordId = int(request.form["wordId"])
    cur.execute(f"SELECT word FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        abort(404)
    word = decode(d[0][0])
    
    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE wordId = {wordId} AND updateTo <= 0 AND userId = {userId}")
    d = cur.fetchall()[0]
    astatus = d[0] # how it is added
    ats = d[1] # addition timestamp

    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()

    status = 1

    tagcnt = 0
    lsttag = 0
    untagcnt = 0
    lstuntag = 0

    delcnt = 0
    lstdel = 0
    undelcnt = 0
    lstundel = 0

    for i in range(2, len(d)):
        if status == 1 and d[i][0] == 2:
            tagcnt += 1
            lsttag = d[i][1]
        elif status == 2 and d[i][0] == 1:
            untagcnt += 1
            lstuntag = d[i][1]
        elif status == 1 and d[i][0] == 3:
            delcnt += 1
            lstdel = d[i][1]
        elif status == 3 and d[i][0] == 1:
            undelcnt += 1
            lstundel = d[i][1]
        status = d[i][0]
    
    cur.execute(f"SELECT nextChallenge, lastChallenge FROM ChallengeData WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()[0]
    nxt = d[0]
    lst = d[1]

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    appeared = len(d)
    mem = 0
    lstmem = 0
    fgt = 0
    lstfgt = 0
    for dd in d:
        if dd[0] == 1:
            mem += 1
            lstmem = dd[1]
        elif dd[0] == 0:
            fgt += 1
            lstfgt = dd[1]
    lst30d = 0
    lst30dmem = 0
    lst7d = 0
    lst7dmem = 0
    lst1d = 0
    lst1dmem = 0
    for dd in d:
        if (time.time() - dd[1]) <= 86401*30:
            lst30d += 1
            lst30dmem += dd[0]
        if (time.time() - dd[1]) <= 86401*7:
            lst7d += 1
            lst7dmem += dd[0]
        if (time.time() - dd[1]) <= 86401:
            lst1d += 1
            lst1dmem += dd[0]
    
    def ts2dt(ts):
        return datetime.datetime.fromtimestamp(ts)

    res = f"About {word}\n"

    if astatus == 0:
        res += f"Added at {ts2dt(ats)} with .xlsx importer.\n"    
    elif astatus == -1:
        res += f"Added at {ts2dt(ats)} on website.\n"    

    if tagcnt > 0:
        res += f"Tagged for {tagcnt} times\n(Last time: {ts2dt(lsttag)}),\n"
    else:
        res += f"Never tagged,\n"
    if delcnt > 0:
        res += f"Deleted for {delcnt} times\n(Last time: {ts2dt(lstdel)}).\n"
    else:
        res += f"Never deleted.\n"

    res += "\n"

    res += "In Challenge Mode,\n"
    if appeared > 0:
        res += f"It has appeared for {appeared} times,\n"
        if mem > 0:
            if fgt == 0:
                res += f"You remembered it every time. Good job!\n"
            else:
                res += f"While recorded as memorized for {mem} times,\n"
                if fgt > 0:
                    res += f"And recorded as forgotten for {fgt} times.\n"
        else:
            res += f"You never memorized it.\n"
        
        res += "\n"

        # res += f"In the last 30 days,"
        # if lst30d > 0:
        #     res += f"it appeared {lst30d} times\nAnd you remembered it for {lst30dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        # if lst7d > 0:
        #     res += f"it appeared {lst7d} times\nAnd you remembered it for {lst7dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        # if lst1d > 0:
        #     res += f"it appeared {lst1d} times\nAnd you remembered it for {lst1dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        
        res += f"The last time it appeared is at\n{ts2dt(lst)},\n"
        if lstmem < lstfgt:
            res += "And you forgot it that time.\n"
        else:
            res += "And you remembered it that time.\n"

        res += "\n"

        res += f"Normally, it will appear again at around\n{ts2dt(nxt)},\n"
        res += f"If you do Challenge Mode at that time.\n"

        res += "\n"
        res += "[Time in UTC + 0]"

    else:
        res += f"It hasn't appeared yet."
    
    return json.dumps({"msg":res})

def getWordsInWordBook(userId, wordBookId, statusRequirement):
    cur = conn.cursor()
    cur.execute(f"SELECT wordId FROM WordBookData WHERE wordBookId = {wordBookId} AND userId = {userId}")
    wordbook = cur.fetchall()
    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE ({statusRequirement}) AND userId = {userId}")
    words = cur.fetchall()
    d = []
    for word in words:
        if (word[0],) in wordbook:
            d.append(word)
    return d

@app.route("/api/getNext", methods = ['POST'])
def apiGetNext():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordId = -1

    op = {-1: "<", 1: ">"}
    order = {-1: "DESC", 1: "ASC"}
    moveType = int(request.form["moveType"]) # -1: previous, 1: next, 0: random
    if moveType in [-1,1]:
        op = op[moveType]
        order = order[moveType]

    current = -1
    if moveType in [-1, 1]:
        current = int(request.form["wordId"])

    statusRequirement = {1: "status = 1 OR status = 2", 2: "status = 2", 3: "status = 3"}
    status = int(request.form["status"])
    statusRequirement = statusRequirement[status]

    wordBookId = int(request.form["wordBookId"])
    
    if wordBookId == 0:
        if moveType in [-1,1]:
            cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE wordId{op}{current} AND ({statusRequirement}) AND userId = {userId} ORDER BY wordId {order} LIMIT 1")
            d = cur.fetchall()
            if len(d) == 0: # no matching results, then find result from first / end
                cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE ({statusRequirement}) AND userId = {userId} ORDER BY wordId {order} LIMIT 1")
                d = cur.fetchall()

        elif moveType == 0:
            cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE ({statusRequirement}) AND userId = {userId} ORDER BY RANDOM() LIMIT 1")
            d = cur.fetchall()
    
    else:
        d = getWordsInWordBook(userId, wordBookId, statusRequirement)
        if len(d) != 0:
            if moveType == -1:
                lst = d[-1]
                for dd in d:
                    if dd[0] == current:
                        break
                    lst = dd
                d = [lst]

            elif moveType == 1:
                nxt = d[0]
                ok = False
                for dd in d:
                    if ok is True:
                        nxt = dd
                        break
                    if dd[0] == current:
                        ok = True
                d = [nxt]
            
            elif moveType == 0:
                rnd = random.randint(0,len(d)-1)
                d = [d[rnd]]

    if len(d) == 0:
        return json.dumps({"wordId": -1, "word": "[No more word]", "translation": "Maybe change the settings?\nOr check your connection?", "status": 1})

    (wordId, word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

rnd=[1,1,1,1,1,1,1,2,2,2,2,2,2,3,3,3,3,3,3,4]
def getChallengeWordId(userId, wordBookId, nofour = False):
    cur = conn.cursor()
    wordId = -1

    # just an interesting random function
    random.shuffle(rnd)
    t = rnd[random.randint(0,len(rnd)-1)]
    while t == 4 and nofour:
        random.shuffle(rnd)
        t = rnd[random.randint(0,len(rnd)-1)]
    
    cache = getWordsInWordBook(userId, wordBookId, "status = 1")

    if t == 1:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} AND userId = {userId} ORDER BY wordId ASC")
        d1 = cur.fetchall()

        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 2 AND userId = {userId} ORDER BY RANDOM()")
            d2 = cur.fetchall()
            for dd in d2:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    break
        else:
            d = getWordsInWordBook(userId, wordBookId, "status = 2")
            oklist = []
            for dd in d:
                if (dd[0],) in d1:
                    oklist.append(dd[0])
            
            if len(oklist) != 0:
                wordId = oklist[random.randint(0,len(oklist)-1)]

        if wordId == -1:
            t = 2
    
    if t == 2:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE nextChallenge <= {int(time.time())} AND nextChallenge != 0 AND userId = {userId} ORDER BY nextChallenge ASC")
        d1 = cur.fetchall()
        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 AND userId = {userId} ORDER BY wordId ASC")
            d2 = cur.fetchall()
            for dd in d1:
                if (dd[0],) in d2:
                    wordId = dd[0]
                    break
        else:
            d = cache
            for dd in d:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    break
        
        if wordId == -1:
            t = 3
    
    if t == 3:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE nextChallenge = 0 AND userId = {userId} ORDER BY RANDOM() ASC")
        d1 = cur.fetchall()
        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 AND userId = {userId} ORDER BY wordId ASC")
            d2 = cur.fetchall()
            for dd in d1:
                if (dd[0],) in d2:
                    wordId = dd[0]
                    break
        else:
            d = cache
            for dd in d:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    break
        
        if wordId == -1:
            t = 5
    
    if t == 5:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} AND nextChallenge != 0 AND userId = {userId} ORDER BY nextChallenge ASC")
        d1 = cur.fetchall()
        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 AND userId = {userId} ORDER BY wordId ASC")
            d2 = cur.fetchall()
            for dd in d1:
                if (dd[0],) in d2:
                    wordId = dd[0]
                    break
        else:
            d = cache
            for dd in d:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    break
        
        if wordId == -1:
            t = 4
    
    if t == 4 and not nofour:
        cur.execute(f"SELECT wordId FROM WordList WHERE status = 3 AND userId = {userId} ORDER BY RANDOM() LIMIT 1")
        d = cur.fetchall()
        if len(d) != 0:
            if wordBookId == 0:
                wordId = d[0][0]
            
            else:
                cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
                d2 = cur.fetchall()
                for dd in d2:
                    if (dd[0],) in d:
                        wordId = dd[0]
                        break
        
        if wordId == -1:
            wordId = getChallengeWordId(userId, wordBookId, nofour = True)
    
    return wordId

@app.route("/api/getNextChallenge", methods = ['POST'])
def apiGetNextChallenge():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordBookId = int(request.form["wordBookId"])
    wordId = getChallengeWordId(userId, wordBookId)

    if wordId == -1:
        return json.dumps({"wordId": wordId, "word": "Out of challenge", "translation": "You are super!\nNo more challenge can be done!", "status": 1})

    cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    (word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

# addtime = [20 minute, 1 hour, 3 hour, 8 hour, 1 day, 2 day, 5 day, 10 day]
addtime = [300, 1200, 3600, 10800, 28800, 86401, 172800, 432000, 864010]
@app.route("/api/updateChallengeRecord", methods = ['POST'])
def apiUpdateChallengeRecord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordId = int(request.form["wordId"])
    memorized = int(request.form["memorized"])
    getNext = int(request.form["getNext"])
    ts = int(time.time())

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE wordId = {wordId} AND userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()

    cur.execute(f"INSERT INTO ChallengeRecord VALUES ({userId}, {wordId},{memorized},{ts})")
    cur.execute(f"UPDATE ChallengeData SET lastChallenge = {ts} WHERE wordId = {wordId}  AND userId = {userId}")

    if memorized == 1:
        tot = 1
        for dd in d:
            if dd[0] == 1:
                tot += 1
        if tot > 8:
            tot = 8
        cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[tot]} WHERE wordId = {wordId} AND userId = {userId}")

    elif memorized == 0:
        cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[0]} WHERE wordId = {wordId} AND userId = {userId}")
    
    conn.commit()

    if getNext == 1:
        wordBookId = int(request.form["wordBookId"])
        wordId = getChallengeWordId(userId, wordBookId)

        if wordId == -1:
            return json.dumps({"wordId": wordId, "word": "Out of challenge", "translation": "You are super! No more challenge can be done!", "status": 1})

        cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
        d = cur.fetchall()
        (word, translation, status) = d[0]
        word = decode(word)
        translation = decode(translation)

        return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

    else:
        return json.dumps({"success": True})

@app.route("/api/getWordCount", methods = ['POST'])
def apiGetWordCount():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    return json.dumps({"count": str(getWordCount(userId))})

@app.route("/api/updateWordStatus", methods = ['POST'])
def apiUpdateWordStatus():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    words = json.loads(request.form["words"])
    status = int(request.form["status"])

    for wordId in words:
        cur.execute(f"SELECT word FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"succeed": False, "msg": "Word not found!"})

        cur.execute(f"UPDATE WordList SET status = {status} WHERE wordId = {wordId} AND userId = {userId}")

        updateWordStatus(userId, wordId, status)

    conn.commit()

    return json.dumps({"succeed": True})

duplicate = []
@app.route("/api/addWord", methods = ['POST'])
def apiAddWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    word = request.form["word"]
    word = encode(word)

    if not word in duplicate:
        cur.execute(f"SELECT * FROM WordList WHERE word = '{word}' AND userId = {userId}")
        if len(cur.fetchall()) != 0:
            duplicate.append(word)
            return json.dumps({"duplicate":True})
    else:
        duplicate.remove(word)

    translation = request.form["translation"]
    translation = encode(translation)

    wordId = -1
    cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} ORDER BY wordId DESC LIMIT 1")
    d = cur.fetchall()
    if len(d) != 0:
        wordId = d[0][0]

    cur.execute(f"INSERT INTO WordList VALUES ({userId},{wordId+1},'{word}','{translation}',1)")
    cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId+1},0,-1)")
    updateWordStatus(userId, wordId+1,-1)
    updateWordStatus(userId, wordId+1,1)
    conn.commit()

    return json.dumps({"success":True})

@app.route("/api/editWord", methods = ['POST'])
def apiEditWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordId = int(request.form["wordId"])
    word = encode(request.form["word"])
    translation = encode(request.form["translation"])

    cur.execute(f"SELECT * FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word does not exist!"})
    
    cur.execute(f"UPDATE WordList SET word = '{word}' WHERE wordId = {wordId} AND userId = {userId}")
    cur.execute(f"UPDATE WordList SET translation = '{translation}' WHERE wordId = {wordId} AND userId = {userId}")
    conn.commit()

    return json.dumps({"success":True})

@app.route("/api/deleteWord", methods = ['POST'])
def apiDeleteWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    words = json.loads(request.form["words"])

    for wordId in words:
        cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
        d = cur.fetchall()
        ts = int(time.time())
        dd = d[0]
        cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
        cur.execute(f"DELETE FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
        conn.commit()

    return json.dumps({"success": True})


@app.route("/api/clearDeleted", methods = ['POST'])
def apiClearDeleted():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId} AND status = 3")
    d = cur.fetchall()
    ts = int(time.time())
    for dd in d:
        cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
    cur.execute(f"DELETE FROM WordList WHERE userId = {userId} AND status = 3")
    conn.commit()

    return json.dumps({"success": True})





##########
# Data API

@app.route("/importData", methods = ['GET', 'POST'])
def importData():
    cur = conn.cursor()
    if request.method == 'POST':
        if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
            return render_template("import.html", MESSAGE = "Login first!")

        userId = int(request.form["userId"])
        token = request.form["token"]
        if not validateToken(userId, token):
            return render_template("import.html", MESSAGE = "Login first!")

        # Do file check
        if 'file' not in request.files:
            return render_template("import.html", MESSAGE = "Invalid import! E1: No file found")
        
        f = request.files['file']
        if f.filename == '':
            return render_template("import.html", MESSAGE = "Invalid import! E2: Empty file name")

        if not f.filename.endswith(".xlsx"):
            return render_template("import.html", MESSAGE = "Only .xlsx files are supported!")
        
        ts=int(time.time())
        f.save(f"/tmp/data{ts}.xlsx")

        try:
            uploaded = pd.read_excel(f"/tmp/data{ts}.xlsx")
            if list(uploaded.keys()).count("Word") != 1 or list(uploaded.keys()).count("Translation")!=1:
                os.system(f"rm -f /tmp/data{ts}.xlsx")
                return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Translation'!")
        except:
            os.system(f"rm -f /tmp/data{ts}.xlsx")
            return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Translation'!")
        
        #####
        
        updateType = request.form["updateType"]
        yesno = {"yes": True, "no": False}
        checkDuplicate = request.form["checkDuplicate"]
        checkDuplicate = yesno[checkDuplicate]

        newlist = pd.read_excel(f"/tmp/data{ts}.xlsx")
        duplicate = []
        cur.execute(f"SELECT word FROM WordList WHERE userId = {userId}")
        wordList = cur.fetchall()
        for i in range(0, len(newlist)):
            if (encode(str(newlist["Word"][i])),) in wordList:
                duplicate.append(str(newlist["Word"][i]))

        if checkDuplicate and updateType == "append":
            if len(duplicate) != 0:
                return render_template("import.html", MESSAGE = f"Upload rejected due to duplicated words: {' ; '.join(duplicate)}")

        wordId = 0

        if updateType == "append":
            cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} ORDER BY wordId DESC LIMIT 1")
            d = cur.fetchall()
            if len(d) != 0:
                wordId = d[0][0]

        elif updateType  == "clear_overwrite":
            cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId}")
            d = cur.fetchall()
            ts = int(time.time())
            for dd in d:
                cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId}")
            cur.execute(f"DELETE FROM WordList WHERE userId = {userId}")
            conn.commit()

        for i in range(0, len(newlist)):
            word = str(newlist['Word'][i])
            translation = str(newlist['Translation'][i])

            if word in duplicate and updateType == "overwrite":
                cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} AND word = '{encode(word)}'")
                wid = cur.fetchall()[0][0] # do not use wordId as variable name or it will cause conflict
                cur.execute(f"UPDATE WordList SET translation = '{encode(translation)}' WHERE wordId = {wid} AND userId = {userId}")
                if list(uploaded.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
                    status = StatusTextToStatus[newlist["Status"][i]]
                    cur.execute(f"UPDATE WordList SET status = {status} WHERE wordId = {wid} AND userId = {userId}")
                continue

            status = 0
            wordId += 1
            updateWordStatus(userId, wordId, status)

            status = 1
            if list(uploaded.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
                status = StatusTextToStatus[newlist["Status"][i]]
            updateWordStatus(userId, wordId, status)

            cur.execute(f"INSERT INTO WordList VALUES ({userId},{wordId}, '{encode(word)}', '{encode(translation)}', {status})")
            cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId}, 0, -1)")

        conn.commit()

        os.system(f"rm -f /tmp/data{ts}.xlsx")

        return render_template("import.html", MESSAGE = "Data imported successfully!")

    else:
        return render_template("import.html", MESSAGE = "")

@app.route("/exportData", methods = ['GET', 'POST'])
def exportData():
    cur = conn.cursor()
    if request.method == "POST":
        if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and not request.form["userId"].isdigit():
            return render_template("export.html", MESSAGE = "Login first!")

        userId = int(request.form["userId"])
        token = request.form["token"]
        if not validateToken(userId, token):
            return render_template("export.html", MESSAGE = "Login first!")
        
        exportType = request.form["exportType"]

        if exportType == "xlsx":
            cur.execute(f"SELECT word, translation, status FROM WordList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) == 0:
                return render_template("export.html", MESSAGE = "Empty word list!")
            
            xlsx = pd.DataFrame()
            for dd in d:
                word = pd.DataFrame([[decode(dd[0]), decode(dd[1]), StatusToStatusText[dd[2]]]],columns=["Word","Translation","Status"],index=[len(d)])
                xlsx = xlsx.append(word)

            xlsx.to_excel(f'/tmp/export{userId}.xlsx', sheet_name='Data', index=False)

            return send_file(f"/tmp/export{userId}.xlsx", as_attachment=True)
        
        else:
            os.system(f"cp ./database.db /tmp/export{userId}.db")
            export_conn = sqlite3.connect(f"/tmp/export{userId}.db")
            export_cur = export_conn.cursor()
            export_cur.execute(f"DELETE FROM UserInfo WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM WordList WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM ChallengeData WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM ChallengeRecord WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM DeletedWordList WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM StatusUpdate WHERE userId != {userId}")
            export_conn.commit()

            return send_file(f"/tmp/export{userId}.db", as_attachment=True)


    else:
        return render_template("export.html", MESSAGE = "")

def autoRestart():
    while 1:
        if sessions.errcnt >= 5:
            os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
            sys.exit(0)
        time.sleep(5)

threading.Thread(target = sessions.PendingAccountDeletion).start()
threading.Thread(target = autoRestart).start()

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run("127.0.0.1",8888)