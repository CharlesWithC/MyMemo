# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import Flask, render_template, request, abort, send_file
import os, sys, datetime, time, threading, math
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

# Import config
class Dict2Obj(object):
    def __init__(self, d):
        for key in d:
            if type(d[key]) is dict:
                data = Dict2Obj(d[key])
                setattr(self, key, data)
            else:
                setattr(self, key, d[key])

config = Dict2Obj({
    "server_ip": "127.0.0.1",
    "server_port": 8888,
    
    "default_user_password": "123456",

    "max_user_allowed": -1,
    "max_word_per_user_allowed": -1,

    "allow_register": True,
    "use_invite_system": False
})
if os.path.exists("./config.json"):
    config_txt = open("./config.json","r").read()
    config = Dict2Obj(json.loads(config_txt))

def hashpwd(password):
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt(12)).decode()

def checkpwd(password, hsh):
    return bcrypt.checkpw(password.encode(),hsh.encode())

st="abcdefghjkmnpqrstuvwxy3456789ABCDEFGHJKMNPQRSTUVWXY"
def genCode(length = 8):
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
    cur.execute(f"CREATE TABLE UserEvent (userId INT, event VARCHAR(32), timestamp INT)")
    # Available event: register, login, change_password, delete_account

    # User should be allowed to delete their accounts
    # When a user request to delete his account, his account will be marked as "Pending for deletion",
    # and will be deleted in 14 days. 
    # During the 14 days, user will be allowed to recover the account. (Like Discord)
    # After the 14 days, all of the user's data will be wiped, including UserInfo, WordList, ChallengeData etc
    # But his/her userId will persist forever, while it represents an empty account named "Deleted Account"

    # If user id becomes a negative number, it means this user has been banned

    defaultpwd = hashpwd(config.default_user_password)
    cur.execute(f"INSERT INTO UserInfo VALUES (0,'default','None','{defaultpwd}',0,'{genCode(6)}')")
    cur.execute(f"INSERT INTO UserEvent VALUES (0, 'register', 0)")
    # Default user system's password is 123456
    # Clear default account's password after setup (so it cannot be logged in)
    # NOTE DO NOT DELETE THE DEFAULT ACCOUNT, keep it in the database record

    cur.execute(f"CREATE TABLE Previlege (userId INT, item VARCHAR(32), value INT)")
    # User previlege, such as word_limit, word_book_limit, allow_group_creation, group_member_limit

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
    cur.execute(f"CREATE TABLE WordBookShare (userId INT, wordBookId INT, shareCode VARCHAR(8))")

    cur.execute(f"CREATE TABLE GroupInfo (groupId INT, owner INT, name VARCHAR(256), description VARCHAR(1024), memberLimit INT, groupCode VARCHAR(8))")
    cur.execute(f"CREATE TABLE GroupMember (groupId INT, userId INT, isEditor INT)")
    cur.execute(f"CREATE TABLE GroupWord (groupId INT, groupWordId INT, word VARCHAR(1024), translation VARCHAR(1024))")
    cur.execute(f"CREATE TABLE GroupSync (groupId INT, userId INT, wordIdOfUser INT, wordIdOfGroup INT)") # word book id of user
    cur.execute(f"CREATE TABLE GroupBind (groupId INT, userId INT, wordBookId INT)") # word book id of user
    # Group is used for multiple users to memorize words together
    # One user will make the share, other users join the group with the code and sync the sharer's word book
    # The sharer will become the owner and he / she will be able to select some users to be editors
    # Each time an editor makes an update on the word book, it will be synced to others
    # Normal users are not allowed to edit the word book
    # Editors are also allowed to kick normal users
    # The users will see each other on a list and know everyone's progress
    
    # Anyone is allowed to quit the group at any time, when he / she quit the group, 
    # the word book will become a normal editable word book,
    # but sync & progress share will stop

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

    # cur.execute(f"CREATE TABLE DeletedWordList (userId INT, wordId INT, word VARCHAR(1024), translation VARCHAR(1024), status INT, deleteTimestamp INT)")
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

@app.route("/api/user/register", methods = ['POST'])
def apiRegister():
    if not config.allow_register:
        return json.dumps({"success": False, "msg": "Public register not enabled!"})
        
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId > 0") # banned users are not counted
    userCnt = cur.fetchall()[0][0]
    if config.max_user_allowed != -1 and userCnt >= config.max_user_allowed:
        return json.dumps({"success": False, "msg": "System has reached its limit of maximum registered users. Contact administrator for more information."})

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
    
    inviter = 0
    if config.use_invite_system:
        cur.execute(f"SELECT userId FROM UserInfo WHERE inviteCode = '{invitationCode}'")
        d = cur.fetchall()
        if len(d) == 0:
            return json.dumps({"success": False, "msg": "Invalid invitation code!"})
        inviter = d[0][0]
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {inviter}")
        if cur.fetchall()[0][0] == "@deleted" or inviter < 0: # inviter < 0 => account banned
            return json.dumps({"success": False, "msg": "Invalid invitation code!"})

    inviteCode = genCode(8)

    userId = 1
    try:
        cur.execute(f"SELECT MAX(userId) FROM UserInfo")
        d = cur.fetchall()
        if len(d) != 0 and not d[0][0] is None:
            userId = d[0][0] + 1
        cur.execute(f"SELECT MIN(userId) FROM UserInfo") # invalid user id due to ban
        d = cur.fetchall()
        if len(d) != 0 and not d[0][0] is None:
            userId = max(userId, -d[0][0] + 1)
        cur.execute(f"INSERT INTO UserInfo VALUES ({userId}, '{username}', '{email}', '{encode(password)}', {inviter}, '{inviteCode}')")
        conn.commit()
    except:
        sessions.errcnt += 1
        return json.dumps({"success": False, "msg": "Unknown error occured. Try again later..."})

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'register', {int(time.time())})")

    return json.dumps({"success": True, "msg": "You are registered! Now you can login!"})

recoverAccount = []
@app.route("/api/user/login", methods = ['POST'])
def apiLogin():
    cur = conn.cursor()
    username = request.form["username"]
    password = request.form["password"]
    if not username.replace("_","").isalnum():
        return json.dumps({"success": False, "msg": "Username can only contain alphabets, digits and underscore!"})
    
    d = [-1]
    try:
        cur.execute(f"SELECT userId, password FROM UserInfo WHERE username = '{username}'")
        d = cur.fetchall()
        if len(d) == 0:
            return json.dumps({"success": False, "msg": "User does not exist!"})
        d = d[0]
    except:
        sessions.errcnt += 1
        return json.dumps({"success": False, "msg": "Unknown error occured. Try again later..."})
        
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
    
    if userId < 0:
        return json.dumps({"success": False, "msg": "Account banned. Contact administrator for more information."})

    token = sessions.login(userId)

    isAdmin = False
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        isAdmin = True

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'login', {int(time.time())})")

    return json.dumps({"success": True, "userId": userId, "token": token, "isAdmin": isAdmin})

@app.route("/api/user/logout", methods = ['POST'])
def apiLogout():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        return json.dumps({"success": True})

    userId = int(request.form["userId"])
    token = request.form["token"]
    ret = sessions.logout(userId, token)

    return json.dumps({"success": ret})

@app.route("/api/user/delete", methods = ['POST'])
def apiDeleteAccount():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'delete_account', {int(time.time())})")
    sessions.logout(userId, token)

    return json.dumps({"success": True})

@app.route("/api/user/validate", methods = ['POST'])
def apiValidateToken():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        return json.dumps({"validation": False})
    userId = int(request.form["userId"])
    token = request.form["token"]
    return json.dumps({"validation": validateToken(userId, token)})

@app.route("/api/user/info", methods = ['POST'])
def apiGetUserInfo():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

    cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {userId} AND event = 'register'")
    regts = cur.fetchall()[0][0]
    age = math.ceil((time.time() - regts) / 86400)

    return json.dumps({"username": d[0], "email": d[1], "invitationCode": d[2], "inviter": inviter, "cnt": cnt, "tagcnt": tagcnt, "delcnt": delcnt, "chcnt": chcnt, "age": age})

@app.route("/api/user/changePassword", methods=['POST'])
def apiChangePassword():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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
    
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'change_password', {int(time.time())})")
    sessions.logoutAll(userId)

    return json.dumps({"success": True})





##########
# Admin API

@app.route("/api/admin/restart", methods = ['POST'])
def apiAdminRestart():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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
# Word Book API

@app.route("/api/wordBook", methods = ['POST'])
def apiGetWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []

    words = []
    cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId}")
    t = cur.fetchall()
    for tt in t:
        words.append(tt[0])
    
    cur.execute(f"SELECT shareCode FROM WordBookShare WHERE wordBookId = 0 AND userId = {userId}")
    t = cur.fetchall()
    shareCode = ""
    if len(t) != 0:
        shareCode = "!"+t[0][0]
    
    ret.append({"wordBookId": 0, "name": "All words", "words": words, "shareCode": shareCode, "groupId": -1, "groupCode": "", "isGroupOwner": False})

    cur.execute(f"SELECT wordBookId, name FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        words = []
        cur.execute(f"SELECT wordId FROM WordBookData WHERE wordBookId = {dd[0]} AND userId = {userId}")
        t = cur.fetchall()
        for tt in t:
            words.append(tt[0])

        cur.execute(f"SELECT shareCode FROM WordBookShare WHERE wordBookId = {dd[0]} AND userId = {userId}")
        t = cur.fetchall()
        shareCode = ""
        if len(t) != 0:
            shareCode = "!" + t[0][0]
        
        cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {dd[0]}")
        t = cur.fetchall()
        groupId = -1
        gcode = ""
        if len(t) != 0:
            groupId = t[0][0]
            cur.execute(f"SELECT groupCode FROM GroupInfo WHERE groupId = {groupId}")
            gcode = "@" + cur.fetchall()[0][0]
        
        isGroupOwner = False
        if groupId != -1:
            cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
            owner = cur.fetchall()[0][0]
            if owner == userId:
                isGroupOwner = True

        ret.append({"wordBookId": dd[0], "name": decode(dd[1]), "words": words, "shareCode": shareCode, "groupId": groupId, "groupCode": gcode, "isGroupOwner": isGroupOwner})
    
    return json.dumps(ret)

@app.route("/api/wordBook/create", methods = ['POST'])
def apiCreateWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    name = str(request.form["name"])

    wordBookId = 1
    cur.execute(f"SELECT MAX(wordBookId) FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and not d[0][0] is None:
        wordBookId = d[0][0] + 1
    cur.execute(f"SELECT MIN(wordBookId) FROM WordBook WHERE userId = {userId}") # invalid word books with negative ids
    d = cur.fetchall()
    if len(d) != 0 and not d[0][0] is None:
        wordBookId = max(wordBookId, -d[0][0] + 1)

    if name.startswith("!") and name[1:].isalnum():
        name = name[1:]
        cur.execute(f"SELECT userId, wordBookId FROM WordBookShare WHERE shareCode = '{name}'")
        d = cur.fetchall()
        if len(d) != 0:
            sharerUserId = d[0][0]
            sharerWordBookId = d[0][1]
            
            cur.execute(f"SELECT username FROM UserInfo WHERE userId = {sharerUserId}")
            sharerUsername = cur.fetchall()[0][0]
            name = encode(sharerUsername + "'s word book")
            if sharerWordBookId != 0:
                # create word book
                cur.execute(f"SELECT name FROM WordBook WHERE userId = {sharerUserId} AND wordBookId = {sharerWordBookId}")
                name = cur.fetchall()[0][0]

            t = []
            if sharerWordBookId != 0:
                cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {sharerUserId} AND wordBookId = {sharerWordBookId}")
                t = cur.fetchall()
            else:
                cur.execute(f"SELECT wordId FROM WordList WHERE userId = {sharerUserId}")
                t = cur.fetchall()
            cur.execute(f"SELECT wordId, word, translation FROM WordList WHERE userId = {sharerUserId}")
            b = cur.fetchall()
            di = {}
            for bb in b:
                di[bb[0]] = (bb[1], bb[2])
            
            max_allow = config.max_word_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_allow != -1 and d[0][0] + len(t) >= max_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help."})

            max_book_allow = config.max_word_book_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_book_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_book_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordBook WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_book_allow != -1 and d[0][0] + len(t) >= max_book_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created word book {max_allow}. Remove some word books (this will not remove the words) or contact administrator for help."})

            # do import
            cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")

            wordId = 0

            cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} ORDER BY wordId DESC LIMIT 1")
            d = cur.fetchall()
            if len(d) != 0:
                wordId = d[0][0]
            
            wordId += 1
            for tt in t:
                cur.execute(f"SELECT wordId, translation FROM WordList WHERE userId = {userId} AND word = '{di[tt[0]][0]}'")
                p = cur.fetchall()
                ctn = False
                for pp in p:
                    if pp[1] == di[tt[0]][1]: # word completely the same
                        cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {pp[0]})")
                        ctn = True
                        break
                if ctn:
                    continue

                cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
                cur.execute(f"INSERT INTO WordList VALUES ({userId}, {wordId}, '{di[tt[0]][0]}', '{di[tt[0]][1]}', 1)")
                cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId}, 0, -1)")

                updateWordStatus(userId, wordId, -1) # -1 is imported word
                updateWordStatus(userId, wordId, 1) # 1 is default status

                wordId += 1
            
            conn.commit()
            return json.dumps({"success": True})
        
        else:
            return json.dumps({"success": False, "msg": "Invalid share code!"})
    
    elif name.startswith("@") and name[1:].isalnum():
        if name == "@pvtgroup":
            return json.dumps({"success": False, "msg": "This is the general code of all private code and it cannot be used!"})
        name = name[1:]
        cur.execute(f"SELECT groupId, name FROM GroupInfo WHERE groupCode = '{name}'")
        d = cur.fetchall()
        if len(d) != 0:
            groupId = d[0][0]
            name = d[0][1]

            cur.execute(f"SELECT memberLimit FROM GroupInfo WHERE groupId = {groupId}")
            mlmt = cur.fetchall()[0][0]
            cur.execute(f"SELECT * FROM GroupMember WHERE groupId = {groupId}")
            if len(cur.fetchall()) >= mlmt:
                return json.dumps({"success": False, "msg": "Group is full!"})

            cur.execute(f"SELECT word, translation, groupWordId FROM GroupWord WHERE groupId = {groupId}")
            t = cur.fetchall()
            
            # preserve limit check here as if the owner dismissed the group, the words will remain in users' lists
            max_allow = config.max_word_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_allow != -1 and d[0][0] + len(t) >= max_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help."})

            max_book_allow = config.max_word_book_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_book_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_book_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordBook WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_book_allow != -1 and d[0][0] + len(t) >= max_book_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created word book {max_allow}. Remove some word books (this will not remove the words) or contact administrator for help."})


            # do import
            cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")
            cur.execute(f"INSERT INTO GroupMember VALUES ({groupId}, {userId}, 0)")

            wordId = 0

            cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} ORDER BY wordId DESC LIMIT 1")
            d = cur.fetchall()
            if len(d) != 0:
                wordId = d[0][0]

            cur.execute(f"INSERT INTO GroupBind VALUES ({groupId}, {userId}, {wordBookId})")
            
            wordId += 1
            for tt in t:
                # no duplicate check as user are not allowed to edit words in group
                cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
                cur.execute(f"INSERT INTO WordList VALUES ({userId}, {wordId}, '{tt[0]}', '{tt[1]}', 1)")
                cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId}, 0, -1)")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {wordId}, {tt[2]})")

                updateWordStatus(userId, wordId, -1) # -1 is imported word
                updateWordStatus(userId, wordId, 1) # 1 is default status

                wordId += 1
            
            conn.commit()
            return json.dumps({"success": True})
        
        else:
            return json.dumps({"success": False, "msg": "Invalid group code!"})


    name = encode(name)
    
    max_book_allow = config.max_word_book_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_book_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_book_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_book_allow != -1 and d[0][0] + len(t) >= max_book_allow:
        return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created word book {max_allow}. Remove some word books (this will not remove the words) or contact administrator for help."})

    cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")
    conn.commit()
    
    return json.dumps({"success": True})

@app.route("/api/wordBook/delete", methods = ['POST'])
def apiDeleteWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["wordBookId"])
    cur.execute(f"SELECT name FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]

    if groupId != -1:
        cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
        d = cur.fetchall()
        if len(d) == 0:
            return json.dumps({"success": False, "msg": "Group does not exist!"})
        owner = d[0][0]
        if userId == owner:
            return json.dumps({"success": False, "msg": "You are the owner of the group. You have to transfer group ownership before deleting the word book."})

        cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId} AND userId = {userId}")
        

    cur.execute(f"DELETE FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/wordBook/addWord", methods = ['POST'])
def apiAddToWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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
        
    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})
    
    cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()

    cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    t = cur.fetchall()

    for wordId in words:
        if (wordId,) in d and not (wordId,) in t:
            cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
            d.append((wordId,))
            t.append((wordId,))

            if groupId != -1:
                cur.execute(f"SELECT word, translation FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
                p = cur.fetchall()[0]
                word = p[0]
                translation = p[1]

                cur.execute(f"SELECT MAX(groupWordId) FROM GroupWord WHERE groupId = {groupId}")
                p = cur.fetchall()
                gwordId = 1
                if len(p) != 0:
                    gwordId = p[0][0] + 1
                cur.execute(f"INSERT INTO GroupWord VALUES ({groupId}, {gwordId}, '{word}', '{translation}')")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {wordId}, {gwordId})")
                
                cur.execute(f"SELECT userId, wordBookId FROM GroupBind WHERE groupId = {groupId}")
                t = cur.fetchall()
                for tt in t:
                    uid = tt[0]
                    if uid == userId:
                        continue
                    wbid = tt[1]
                    wid = 1
                    cur.execute(F"SELECT MAX(wordId) FROM WordList WHERE userId = {uid}")
                    p = cur.fetchall()
                    if len(p) != 0:
                        wid = p[0][0] + 1
                    cur.execute(f"INSERT INTO WordList VALUES ({uid}, {wid}, '{word}', '{translation}', 1)")
                    cur.execute(f"INSERT INTO WordBookData VALUES ({uid}, {wbid}, {wid})")
                    cur.execute(f"INSERT INTO ChallengeData VALUES ({uid},{wid},0,-1)")
                    cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {uid}, {wid}, {gwordId})")
                    updateWordStatus(uid, wid, -3) # -3 is group word
                    updateWordStatus(uid, wid, 1) # 1 is default status
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/wordBook/deleteWord", methods = ['POST'])
def apiDeleteFromWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

    
    cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()

    for wordId in words:
        if (wordId,) in d:
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId} AND wordId = {wordId}")
            
            if groupId != -1:
                cur.execute(f"SELECT wordIdOfGroup FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
                gwordId = cur.fetchall()
                if len(gwordId) == 0:
                    continue
                gwordId = gwordId[0][0]
                cur.execute(f"DELETE FROM GroupWord WHERE groupId = {groupId} AND groupWordId = {gwordId}")
                cur.execute(f"SELECT userId, wordIdOfUser FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
                t = cur.fetchall()
                for tt in t:
                    uid = tt[0]
                    if uid == userId:
                        continue
                    wid = tt[1]
                    cur.execute(f"DELETE FROM WordList WHERE userId = {uid} AND wordId = {wid}")
                    cur.execute(f"DELETE FROM WordBookData WHERE userId = {uid} AND wordId = {wid}")
                cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
                cur.execute(f"DELETE FROM GroupWord WHERE groupWordId = {gwordId}")
    
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/wordBook/wordList", methods = ['POST'])
def apiGetWordList():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

@app.route("/api/wordBook/share", methods = ['POST'])
def apiShareWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["wordBookId"])
    op = request.form["operation"]

    if op == "share":
        cur.execute(f"SELECT * FROM WordBookShare WHERE userId = {userId} AND wordBookId = {wordBookId}")
        if len(cur.fetchall()) != 0:
            return json.dumps({"success": False, "msg": "Word book already shared!"})
        else:
            shareCode = genCode(8)
            cur.execute(f"SELECT * FROM WordBookShare WHERE shareCode = '{shareCode}'")
            if len(cur.fetchall()) != 0: # conflict
                for _ in range(10):
                    shareCode = genCode(8)
                    cur.execute(f"SELECT * FROM WordBookShare WHERE shareCode = '{shareCode}'")
                    if len(cur.fetchall()) == 0:
                        break
                cur.execute(f"SELECT * FROM WordBookShare WHERE shareCode = '{shareCode}'")
                if len(cur.fetchall()) != 0:
                    return json.dumps({"success": False, "msg": "Unable to generate an unique share code..."})
                    
            cur.execute(f"INSERT INTO WordBookShare VALUES ({userId}, {wordBookId}, '{shareCode}')")
            conn.commit()
            return json.dumps({"success": True, "msg": f"Done! Share code: !{shareCode}. Tell your friend to enter it in the textbox of 'Create Word Book' and he / she will be able to import it!", "shareCode": f"!{shareCode}"})
    
    elif op == "unshare":
        cur.execute(f"SELECT * FROM WordBookShare WHERE userId = {userId} AND wordBookId = {wordBookId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"success": False, "msg": "Word book not shared!"})
        else:
            cur.execute(f"DELETE FROM WordBookShare WHERE userId = {userId} AND wordBookId = {wordBookId}")
            conn.commit()
            return json.dumps({"success": True, "msg": "Word book unshared!"})

@app.route("/api/wordBook/rename", methods = ['POST'])
def apiRenameWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["wordBookId"])
    newName = str(request.form["name"])

    cur.execute(f"SELECT * FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})

    cur.execute(f"UPDATE WordBook SET name = '{encode(newName)}' WHERE userId = {userId} AND wordBookId = {wordBookId}")
    conn.commit()
    return json.dumps({"success": True})






##########
# Group API

@app.route("/api/group", methods = ['POST'])
def apiGroup():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    op = request.form["operation"]

    if op == "create":
        allow = config.allow_group_creation_for_all_user
        cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'allow_group_creation'")
        pr = cur.fetchall()
        if len(pr) != 0:
            allow = pr[0][0]
        if not allow:
            return json.dumps({"success": False, "msg": f"You are not allowed to create groups. Contact administrator for help."})

        wordBookId = int(request.form["wordBookId"])
        name = encode(request.form["name"])
        description = encode(request.form["description"])

        groupId = 1
        cur.execute(f"SELECT MAX(groupId) FROM GroupInfo")
        d = cur.fetchall()
        if len(d) != 0 and not d[0][0] is None:
            groupId = d[0][0] + 1
        cur.execute(f"SELECT MIN(groupId) FROM GroupInfo") # invalid group id due to deletion
        d = cur.fetchall()
        if len(d) != 0 and not d[0][0] is None:
            groupId = max(groupId, -d[0][0] + 1)

        lmt = config.max_group_member
        cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'group_member_limit'")
        pr = cur.fetchall()
        if len(pr) != 0:
            lmt = pr[0][0]

        gcode = genCode(8)
        cur.execute(f"INSERT INTO GroupInfo VALUES ({groupId}, {userId}, '{name}', '{description}', {lmt}, '{gcode}')")
        cur.execute(f"INSERT INTO GroupMember VALUES ({groupId}, {userId}, 1)")
        cur.execute(f"INSERT INTO GroupBind VALUES ({groupId}, {userId}, {wordBookId})")
        cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
        words = cur.fetchall()
        gwordId = 1
        for word in words:
            wordId = word[0]
            cur.execute(f"SELECT word, translation FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
            d = cur.fetchall()[0]
            cur.execute(f"INSERT INTO GroupWord VALUES ({groupId}, {gwordId}, '{d[0]}', '{d[1]}')")
            cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {wordId}, {gwordId})")
            gwordId += 1
        conn.commit()

        return json.dumps({"success": True, "msg": f"Group created! Group code: @{gcode}. Tell your friends to create a word book with this code and they will join your group automatically.", \
            "groupId": groupId, "groupCode": f"@{gcode}", "isGroupOwner": True})

    elif op == "dismiss":
        groupId = int(request.form["groupId"])
        cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
        owner = cur.fetchall()
        if len(owner) == 0:
            return json.dumps({"success": False, "msg": f"Group not found!"})
        owner = owner[0][0]

        if owner != userId:
            return json.dumps({"success": False, "msg": f"You are not the owner of the group!"})
        
        cur.execute(f"UPDATE GroupInfo SET groupId = {-groupId} WHERE groupId = {groupId}")
        cur.execute(f"UPDATE GroupMember SET groupId = {-groupId} WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupWord WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId}")
        conn.commit()

        return json.dumps({"success": True, "msg": f"Group dismissed! Word book sync stopped and members are not able to see others' progress."})

@app.route("/api/group/quit", methods = ['POST'])
def apiQuitGroup():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    groupId = int(request.form["groupId"])

    cur.execute(f"SELECT * FROM GroupMember WHERE userId = {userId} AND groupId = {groupId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "You are not in the group!"})
    
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Group does not exist!"})
    owner = d[0][0]
    if userId == owner:
        return json.dumps({"success": False, "msg": "You are the owner of the group. You have to transfer group ownership before quiting the group."})

    cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {userId}")
    cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
    cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId} AND userId = {userId}")

    conn.commit()

    return json.dumps({"success": True, "msg": "You have quit the group successfully! The word book has became a local one."})

@app.route("/api/group/code/update", methods = ['POST'])
def apiGroupCodeUpdate():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    groupId = int(request.form["groupId"])
    
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Group does not exist!"})
    owner = d[0][0]
    if userId != owner:
        return json.dumps({"success": False, "msg": "You are not the owner of the group!"})

    op = request.form["operation"]

    if op == "disable":
        cur.execute(f"UPDATE GroupInfo SET groupCode = 'pvtgroup' WHERE groupId = {groupId}")
        conn.commit()
        return json.dumps({"success": True, "msg": "Group has been made to private and no user is allowed to join!", "groupCode": "@pvtgroup"})
    
    elif op == "revoke":
        gcode = genCode(8)
        cur.execute(f"UPDATE GroupInfo SET groupCode = '{gcode}' WHERE groupId = {groupId}")
        conn.commit()
        return json.dumps({"success": True, "msg": f"New group code: @{gcode}", "groupCode": f"@{gcode}"})


# Get Group User Progress Info
# Owner manage member (kick / editor) (In the user list page)




##########
# Word API

@app.route("/api/word", methods = ['POST'])
def apiGetWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

@app.route("/api/word/id", methods = ['POST'])
def apiGetWordID():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    word = request.form["word"].replace("\n","\\n")
    wordBookId = int(request.form["wordBookId"])
    cur.execute(f"SELECT wordId FROM WordList WHERE word = '{encode(word)}' AND userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0:
        wordId = d[0][0]
        if wordBookId > 0:
            cur.execute(f"SELECT wordBookId FROM WordBookData WHERE wordId = {wordId} AND wordBookId = {wordBookId}")
            if len(cur.fetchall()) == 0:
                abort(404)

        # If there are multiple records, then return the first one
        # NOTE: The user should be warned when they try to insert multiple records with the same word
        return json.dumps({"wordId" : wordId})
    else:
        abort(404)

@app.route("/api/word/stat", methods = ['POST'])
def apiGetWordStat():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

@app.route("/api/word/next", methods = ['POST'])
def apiGetNext():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

@app.route("/api/word/challenge/next", methods = ['POST'])
def apiGetNextChallenge():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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
@app.route("/api/word/challenge/update", methods = ['POST'])
def apiUpdateChallengeRecord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

@app.route("/api/word/count", methods = ['POST'])
def apiGetWordCount():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    return json.dumps({"count": str(getWordCount(userId))})

@app.route("/api/word/status/update", methods = ['POST'])
def apiUpdateWordStatus():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    words = json.loads(request.form["words"])
    status = int(request.form["status"])

    if status < 1 or status > 3:
        return json.dumps({"success": False, "msg": "Invalid status code!"})

    for wordId in words:
        cur.execute(f"SELECT word FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"succeed": False, "msg": "Word not found!"})

        cur.execute(f"UPDATE WordList SET status = {status} WHERE wordId = {wordId} AND userId = {userId}")

        updateWordStatus(userId, wordId, status)

    conn.commit()

    return json.dumps({"succeed": True})

duplicate = []
@app.route("/api/word/add", methods = ['POST'])
def apiAddWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["addToWordBook"])
    groupId = -1
    if wordBookId != 0:
        cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
        d = cur.fetchall()
        if len(d) != 0:
            groupId = d[0][0]
            cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
            isEditor = cur.fetchall()[0][0]
            if isEditor == 0:
                return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

    max_allow = config.max_word_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_allow != -1 and d[0][0] + 1>= max_allow:
        return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help."})

    word = request.form["word"].replace("\\n","\n")
    word = encode(word)

    if not (userId, word) in duplicate:
        cur.execute(f"SELECT * FROM WordList WHERE word = '{word}' AND userId = {userId}")
        if len(cur.fetchall()) != 0:
            duplicate.append((userId, word))
            return json.dumps({"success": False, "msg": "Word duplicated! Add again to ignore."})
    else:
        duplicate.remove((userId, word))

    translation = request.form["translation"].replace("\\n","\n")
    translation = encode(translation)

    wordId = -1
    cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} ORDER BY wordId DESC LIMIT 1")
    d = cur.fetchall()
    if len(d) != 0:
        wordId = d[0][0]
    wordId += 1

    cur.execute(f"INSERT INTO WordList VALUES ({userId},{wordId},'{word}','{translation}',1)")
    cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId},0,-1)")
    updateWordStatus(userId, wordId, -2) # -2 is website added word
    updateWordStatus(userId, wordId, 1)

    if wordBookId != -1:
        cur.execute(f"SELECT wordBookId FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
        if len(cur.fetchall()) != 0:
            cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
    
    if groupId != -1:
        cur.execute(f"SELECT MAX(groupWordId) FROM GroupWord WHERE groupId = {groupId}")
        gwordId = cur.fetchall()[0][0] + 1
        cur.execute(f"INSERT INTO GroupWord VALUES ({groupId}, {gwordId}, '{word}', '{translation}')")
        cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {wordId}, {gwordId})")
        
        cur.execute(f"SELECT userId, wordBookId FROM GroupBind WHERE groupId = {groupId}")
        t = cur.fetchall()
        for tt in t:
            uid = tt[0]
            if uid == userId:
                continue
            wbid = tt[1]
            wid = 1
            cur.execute(F"SELECT MAX(wordId) FROM WordList WHERE userId = {uid}")
            p = cur.fetchall()
            if len(p) != 0:
                wid = p[0][0] + 1
            cur.execute(f"INSERT INTO WordList VALUES ({uid}, {wid}, '{word}', '{translation}', 1)")
            cur.execute(f"INSERT INTO WordBookData VALUES ({uid}, {wbid}, {wid})")
            cur.execute(f"INSERT INTO ChallengeData VALUES ({uid},{wid},0,-1)")
            cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {uid}, {wid}, {gwordId})")
            updateWordStatus(uid, wid, -3) # -3 is group word
            updateWordStatus(uid, wid, 1) # 1 is default status

    conn.commit()

    return json.dumps({"success": True, "msg": "Word added!"})

@app.route("/api/word/edit", methods = ['POST'])
def apiEditWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordId = int(request.form["wordId"])

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

    word = encode(request.form["word"].replace("\\n","\n"))
    translation = encode(request.form["translation"].replace("\\n","\n"))

    cur.execute(f"SELECT * FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word does not exist!"})
    
    cur.execute(f"UPDATE WordList SET word = '{word}' WHERE wordId = {wordId} AND userId = {userId}")
    cur.execute(f"UPDATE WordList SET translation = '{translation}' WHERE wordId = {wordId} AND userId = {userId}")

    if groupId != -1:
        cur.execute(f"SELECT wordIdOfGroup FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
        gwordId = cur.fetchall()[0][0]
        cur.execute(f"UPDATE GroupWord SET word = '{word}' WHERE groupId = {groupId} AND groupWordId = {gwordId}")
        cur.execute(f"UPDATE GroupWord SET translation = '{translation}' WHERE groupId = {groupId} AND groupWordId = {gwordId}")
        cur.execute(f"SELECT userId, wordIdOfUser FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
        t = cur.fetchall()
        for tt in t:
            uid = tt[0]
            if uid == userId:
                continue
            wid = tt[1]
            cur.execute(f"UPDATE WordList SET word = '{word}' WHERE userId = {uid} AND wordId = {wid}")
            cur.execute(f"UPDATE WordList SET translation = '{translation}' WHERE userId = {uid} AND wordId = {wid}")

    conn.commit()

    return json.dumps({"success":True})

@app.route("/api/word/delete", methods = ['POST'])
def apiDeleteWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    words = json.loads(request.form["words"])

    for wordId in words:
        groupId = -1
        cur.execute(f"SELECT groupId FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
        d = cur.fetchall()
        if len(d) != 0:
            groupId = d[0][0]
            cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
            isEditor = cur.fetchall()[0][0]
            if isEditor == 0:
                return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

        cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
        d = cur.fetchall()
        if len(d) > 0: # make sure word not deleted
            ts = int(time.time())
            dd = d[0]
            # cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
            cur.execute(f"DELETE FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordId = {wordId}")
            
        if groupId != -1:
            cur.execute(f"SELECT wordIdOfGroup FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
            gwordId = cur.fetchall()[0][0]
            cur.execute(f"DELETE FROM GroupWord WHERE groupId = {groupId} AND groupWordId = {gwordId}")
            cur.execute(f"SELECT userId, wordIdOfUser FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
            t = cur.fetchall()
            for tt in t:
                uid = tt[0]
                if uid == userId:
                    continue
                wid = tt[1]
                cur.execute(f"DELETE FROM WordList WHERE userId = {uid} AND wordId = {wid}")
                cur.execute(f"DELETE FROM WordBookData WHERE userId = {uid} AND wordId = {wid}")
            cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
            cur.execute(f"DELETE FROM GroupWord WHERE groupWordId = {gwordId}")

    conn.commit()

    return json.dumps({"success": True})


@app.route("/api/word/clearDeleted", methods = ['POST'])
def apiClearDeleted():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId} AND status = 3")
    d = cur.fetchall()
    ts = int(time.time())
    cur.execute(f"DELETE FROM WordList WHERE userId = {userId} AND status = 3")
    # for dd in d:
    #     cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
    for dd in d:
        cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordId = {dd[0]}")
    conn.commit()

    return json.dumps({"success": True})





##########
# Data API

@app.route("/importData", methods = ['GET', 'POST'])
def importData():
    cur = conn.cursor()
    if request.method == 'POST':
        if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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
        f.save(f"/tmp/WordMemoCache/data{ts}.xlsx")

        try:
            uploaded = pd.read_excel(f"/tmp/WordMemoCache/data{ts}.xlsx")
            if list(uploaded.keys()).count("Word") != 1 or list(uploaded.keys()).count("Translation")!=1:
                os.system(f"rm -f /tmp/WordMemoCache/data{ts}.xlsx")
                return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Translation'!")
        except:
            os.system(f"rm -f /tmp/WordMemoCache/data{ts}.xlsx")
            return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Translation'!")
        
        #####
        
        updateType = request.form["updateType"]
        yesno = {"yes": True, "no": False}
        checkDuplicate = request.form["checkDuplicate"]
        checkDuplicate = yesno[checkDuplicate]

        newlist = pd.read_excel(f"/tmp/WordMemoCache/data{ts}.xlsx")
        importDuplicate = []
        cur.execute(f"SELECT word FROM WordList WHERE userId = {userId}")
        wordList = cur.fetchall()
        for i in range(0, len(newlist)):
            if (encode(str(newlist["Word"][i])),) in wordList:
                importDuplicate.append(str(newlist["Word"][i]))

        if checkDuplicate and updateType == "append":
            if len(importDuplicate) != 0:
                return render_template("import.html", MESSAGE = f"Upload rejected due to duplicated words: {' ; '.join(importDuplicate)}")

        
        max_allow = config.max_word_per_user_allowed
        cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
        pr = cur.fetchall()
        if len(pr) != 0:
            max_allow = pr[0][0]
        cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) != 0 and max_allow != -1 and d[0][0] + len(newlist) >= max_allow:
            return render_template("import.html", MESSAGE = f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help.")


        wordId = 0

        cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} ORDER BY wordId DESC LIMIT 1")
        d = cur.fetchall()
        if len(d) != 0:
            wordId = d[0][0]

        if updateType  == "clear_overwrite":
            cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) > 0:
                ts = int(time.time())
                # for dd in d:
                #     cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
                cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId}")
                cur.execute(f"DELETE FROM WordList WHERE userId = {userId}")
        conn.commit()

        wordBookId = int(request.form["wordBookId"])
        wordBookList = []
        if wordBookId != 0:
            cur.execute(f"SELECT wordBookId FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
            if len(cur.fetchall()) == 0:
                wordBookId = 0
            else:
                cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
                wordBookList = cur.fetchall()

        for i in range(0, len(newlist)):
            word = str(newlist['Word'][i]).replace("\\n","\n")
            translation = str(newlist['Translation'][i]).replace("\\n","\n")

            if word in importDuplicate and updateType == "overwrite":
                cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} AND word = '{encode(word)}'")
                wid = cur.fetchall()[0][0] # do not use wordId as variable name or it will cause conflict
                cur.execute(f"UPDATE WordList SET translation = '{encode(translation)}' WHERE wordId = {wid} AND userId = {userId}")
                if list(uploaded.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
                    status = StatusTextToStatus[newlist["Status"][i]]
                    cur.execute(f"UPDATE WordList SET status = {status} WHERE wordId = {wid} AND userId = {userId}")
                if wordBookId != 0:
                    if not (wordId,) in wordBookList:
                        cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
                        wordBookList.append((wordId,))
                    else:
                        cur.execute(f"UPDATE WordBookData SET wordBookId = {wordBookId} WHERE userId = {userId} AND wordId = {wordId}")
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

            updateWordStatus(userId, wordId, -4) # -1 is shared word
            updateWordStatus(userId, wordId, 1) # 1 is default status
            
            if wordBookId != 0:
                cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")

        conn.commit()

        os.system(f"rm -f /tmp/WordMemoCache/data{ts}.xlsx")

        return render_template("import.html", MESSAGE = "Data imported successfully!")

    else:
        return render_template("import.html", MESSAGE = "")

@app.route("/exportData", methods = ['GET', 'POST'])
def exportData():
    cur = conn.cursor()
    if request.method == "POST":
        if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
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

            xlsx.to_excel(f'/tmp/WordMemoCache/export{userId}.xlsx', sheet_name='Data', index=False)

            return send_file(f"/tmp/WordMemoCache/export{userId}.xlsx", as_attachment=True)
        
        else:
            os.system(f"cp ./database.db /tmp/WordMemoCache/export{userId}.db")
            export_conn = sqlite3.connect(f"/tmp/WordMemoCache/export{userId}.db")
            export_cur = export_conn.cursor()
            export_cur.execute(f"DROP TABLE AdminList")
            export_cur.execute(f"DROP TABLE Previlege")
            export_cur.execute(f"DROP TABLE UserInfo")
            export_cur.execute(f"DROP TABLE UserEvent")
            export_cur.execute(f"DELETE FROM WordBook WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM WordBookData WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM WordBookShare WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM WordList WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM ChallengeData WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM ChallengeRecord WHERE userId != {userId}")
            # export_cur.execute(f"DELETE FROM DeletedWordList WHERE userId != {userId}")
            export_cur.execute(f"DELETE FROM StatusUpdate WHERE userId != {userId}")
            export_conn.commit()

            return send_file(f"/tmp/WordMemoCache/export{userId}.db", as_attachment=True)


    else:
        return render_template("export.html", MESSAGE = "")

def autoRestart():
    while 1:
        if sessions.errcnt >= 5:
            os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
            sys.exit(0)
        time.sleep(5)




##########
# Admin Commands

# Although there is api protection, a reverse proxy authentication is suggested
@app.route("/admin/cli", methods = ['GET'])
def adminCli():    
    return render_template("admincli.html")

@app.route("/api/admin/command", methods = ['POST'])
def apiAdminCommand():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        abort(401)
    
    command = request.form["command"].split(" ")
    if command[0] == "get_user_info":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": f"Usage: get_user_info [userId]\nGet detailed user info of [userId]"})
        
        uid = abs(int(command[1]))
        
        cur.execute(f"SELECT username, email, inviteCode, inviter FROM UserInfo WHERE userId = {uid}")
        d = cur.fetchall()
        banned = False
        if len(d) == 0:
            cur.execute(f"SELECT username, email, inviteCode, inviter FROM UserInfo WHERE userId = {-uid}") # check banned
            d = cur.fetchall()

            if len(d) == 0:
                return json.dumps({"success": False, "msg": f"User not found!"})
            
            banned = True
        
        d = d[0]

        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {d[3]}")
        inviter = cur.fetchall()[0][0]

        cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {uid}")
        cnt = cur.fetchall()[0][0]

        cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {uid} AND event = 'register'")
        regts = cur.fetchall()[0][0]
        age = math.ceil((time.time() - regts) / 86400)

        msg = ""
        if banned:
            msg += "Account has been banned\n"

        return json.dumps({"success": True, "msg": f"{d[0]} (UID: {uid})\nEmail: {d[1]}\nInvitation Code: {d[2]}\nInviter: {inviter} (UID: {d[3]})\nWord Count: {cnt}\nAccount age: {age} day(s)\n{msg}"})
    
    elif command[0] == "create_user":
        if len(command) != 4:
            return json.dumps({"success": False, "msg": f"Usage: create_user [username] [email] [password]\nCreate a user by admin, user will be shown as invited by this admin"})
        
        username = command[1]
        email = command[2]
        password = command[3]
        inviter = userId # inviter is admin
        
        if not username.replace("_","").isalnum():
            return json.dumps({"success": False, "msg": "Username can only contain alphabets, digits and underscore!"})
        if validators.email(email) != True:
            return json.dumps({"success": False, "msg": "Invalid email!"})

        cur.execute(f"SELECT username FROM UserInfo WHERE username = '{username}'")
        if len(cur.fetchall()) != 0:
            return json.dumps({"success": False, "msg": "Username already registered!"})

        password = hashpwd(password)

        inviteCode = genCode()

        uid = 1
        try:
            cur.execute(f"SELECT MAX(userId) FROM UserInfo")
            d = cur.fetchall()
            if len(d) != 0 and not d[0][0] is None:
                uid = d[0][0] + 1
            cur.execute(f"SELECT MIN(userId) FROM UserInfo") # invalid user id due to ban
            d = cur.fetchall()
            if len(d) != 0 and not d[0][0] is None:
                uid = max(uid, -d[0][0] + 1)
            cur.execute(f"INSERT INTO UserInfo VALUES ({uid}, '{username}', '{email}', '{encode(password)}', {inviter}, '{inviteCode}')")
            conn.commit()
        except:
            import traceback
            traceback.print_exc()
            sessions.errcnt += 1
            return json.dumps({"success": False, "msg": "Unknown error occured. Try again later..."})

        cur.execute(f"INSERT INTO UserEvent VALUES ({uid}, 'register', {int(time.time())})")
        conn.commit()

        return json.dumps({"success": True, "msg": f"User registered (UID: {uid})"})
    
    elif command[0] == "delete_user":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: delete_user [userId]\nThe account must be marked as deletion first, and admin will be able to bring the deletion schedule forward"})

        uid = int(command[1])
        ok = sessions.DeleteAccountNow(uid)

        if ok == -1:
            return json.dumps({"success": False, "msg": "Account not marked for deletion!"})
        
        elif ok == 0:
            cur.execute(f"UPDATE UserInfo SET username = '@deleted' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordList WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBook WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBookShare WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeRecord WHERE userId = {uid}")
            cur.execute(f"DELETE FROM StatusUpdate WHERE userId = {uid}")
            return json.dumps({"success": False, "msg": "Account deleted"})
    
    elif command[0] == "set_previlege":
        if len(command) != 4:
            return json.dumps({"success": False, "msg": "Usage: set_previlege [userId] [item] [value]\nAdd [item] previlege for user [userId] ([item] can be word_limit)\nIf previlege exists, then update it"})

        uid = int(command[1])
        item = command[2]
        value = int(command[3])

        if not item in ['word_limit', 'word_book_limit', 'allow_group_creation', 'group_member_limit']:
            return json.dumps({"success": False, "msg": f"Unknown previlege item: {item}. Acceptable item list: word_limit"})

        cur.execute(f"SELECT * FROM Previlege WHERE userId = {uid} AND item = '{item}'")
        if len(cur.fetchall()) == 0:
            cur.execute(f"INSERT INTO Previlege VALUES ({uid}, '{item}', {value})")
        else:
            cur.execute(f"UPDATE Previlege SET value = {value} WHERE userId = {uid} AND item = '{item}'")
        conn.commit()

        return json.dumps({"success": True, "msg": "Previlege set"})
    
    elif command[0] == "remove_previlege":
        if len(command) != 3:
            return json.dumps({"success": False, "msg": "Usage: remove_previlege [userId] [item]\nDelete [item] previlege from user [userId]"})

        uid = int(command[1])
        item = command[2]

        if not item in ['word_limit', 'word_book_limit', 'allow_group_creation', 'group_member_limit']:
            return json.dumps({"success": False, "msg": f"Unknown previlege item: {item}. Acceptable item list: word_limit"})

        cur.execute(f"SELECT * FROM Previlege WHERE userId = {uid} AND item = '{item}'")
        if len(cur.fetchall()) != 0:
            cur.execute(f"DELETE FROM Previlege WHERE userId = {uid} AND item = '{item}'")
            conn.commit()
            return json.dumps({"success": True, "msg": "Previlege removed for this user"})
        else:
            return json.dumps({"success": False, "msg": "This user doesn't have this previlege!"})

    elif command[0] == "ban_account":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: ban_account [userId]\nBan account"})
        
        uid = int(command[1])

        if uid < 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if uid == userId:
            return json.dumps({"success": False, "msg": "You cannot ban yourself!"})

        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {uid}")
        if len(cur.fetchall()) == 0:
            cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
            if len(cur.fetchall()) == 0:
                return json.dumps({"success": False, "msg": "Account doesn't exist!"})
            else:
                return json.dumps({"success": False, "msg": "Account already banned!"})
        
        cur.execute(f"UPDATE UserInfo SET userId = {-uid} WHERE userId = {uid}")
        conn.commit()

        return json.dumps({"success": False, "msg": f"Banned user {uid}"})

    elif command[0] == "unban_account":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: unban_account [userId]\nUnban account"})
        
        uid = int(command[1])

        if uid <= 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})

        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"success": False, "msg": "Account isn't banned!"})
            
        else:
            cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
            if len(cur.fetchall()) == 0:
                return json.dumps({"success": False, "msg": "Account doesn't exist!"})
            else:
                cur.execute(f"UPDATE UserInfo SET userId = {uid} WHERE userId = {-uid}")
                conn.commit()
                return json.dumps({"success": False, "msg": f"Unbanned user {uid}"})

    elif command[0] == "get_user_count":
        cur.execute(f"SELECT COUNT(*) FROM UserInfo")
        tot = 0
        d = cur.fetchall()
        if len(d) != 0:
            tot = d[0][0]
            
        cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId > 0")
        cnt = 0
        d = cur.fetchall()
        if len(d) != 0:
            cnt = d[0][0]
        
        cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE username = '@deleted' AND userId > 0")
        deled = 0
        d = cur.fetchall()
        if len(d) != 0:
            deled = d[0][0]

        cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId < 0")
        banned = 0
        d = cur.fetchall()
        if len(d) != 0:
            banned = d[0][0]
        
        return json.dumps({"success": True, "msg": f"Total user: {tot}\nActive user: {cnt - deled}\nBanned / Banned & Deleted user: {banned}\nDeleted user: {deled}"})

    else:
        return json.dumps({"success": False, "msg": "Unknown command"})

def PendingAccountDeletion():
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
            cur.execute(f"DELETE FROM ChallengeData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeRecord WHERE userId = {uid}")
            cur.execute(f"DELETE FROM StatusUpdate WHERE userId = {uid}")

            conn.commit()

        time.sleep(3600)

def ClearCache():
    while 1:
        recoverAccount = []
        duplicate = []
        os.system("rm -f /tmp/WordMemoCache/*")
        time.sleep(3600) # clear each hour

if not os.path.exists("/tmp/WordMemoCache"):
    os.system("mkdir /tmp/WordMemoCache")

threading.Thread(target = PendingAccountDeletion).start()
threading.Thread(target = autoRestart).start()
threading.Thread(target = ClearCache).start()

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run(config.server_ip, config.server_port)