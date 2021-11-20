# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time, math
import json
import validators

from app import app, config
import db
from functions import *
import sessions

import MySQLdb
import sqlite3
conn = None

def updateconn():
    global conn
    if config.database == "mysql":
        conn = MySQLdb.connect(host = app.config["MYSQL_HOST"], user = app.config["MYSQL_USER"], \
            passwd = app.config["MYSQL_PASSWORD"], db = app.config["MYSQL_DB"])
    elif config.database == "sqlite":
        conn = sqlite3.connect("database.db", check_same_thread = False)
    
updateconn()

##########
# User API

@app.route("/api/user/register", methods = ['POST'])
def apiRegister():
    if not config.allow_register:
        return json.dumps({"success": False, "msg": "Public register not enabled!"})
        
    updateconn()
    cur = conn.cursor()

    userCnt = 0
    cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId > 0") # banned users are not counted
    t = cur.fetchall()
    if len(t) > 0:
        userCnt = t[0][0]
    if config.max_user_allowed != -1 and userCnt >= config.max_user_allowed:
        return json.dumps({"success": False, "msg": "System has reached its limit of maximum registered users. Contact administrator for more information."})

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    invitationCode = request.form["invitationCode"]

    if username is None or email is None or password is None or invitationCode is None \
        or username.replace(" ","") == "" or email.replace(" ","") == "" or password.replace(" ","") == "" or invitationCode.replace(" ","") == "":
        return json.dumps({"success": False, "msg": "All the fields must be filled!"})
    if " " in username or "(" in username or ")" in username or "[" in username or "]" in username or "{" in username or "}" in username \
        or "<" in username or ">" in username \
            or "!" in username or "@" in username or "'" in username or '"' in username or "/" in username or "\\" in username :
        return json.dumps({"success": False, "msg": "Username must not contain: spaces, ( ) [ ] { } < > ! @ ' \" / \\"})
    username = encode(username)
    if validators.email(email) != True:
        return json.dumps({"success": False, "msg": "Invalid email!"})
    if not invitationCode.isalnum():
        return json.dumps({"success": False, "msg": "Invitation code can only contain alphabets and digits!"})

    cur.execute(f"SELECT username FROM UserInfo WHERE username = '{username}'")
    if len(cur.fetchall()) != 0:
        return json.dumps({"success": False, "msg": "Username occupied!"})

    password = hashpwd(password)
    
    inviter = 0
    if config.use_invite_system:
        cur.execute(f"SELECT userId FROM UserInfo WHERE inviteCode = '{invitationCode}'")
        d = cur.fetchall()
        if len(d) == 0:
            return json.dumps({"success": False, "msg": "Invalid invitation code!"})
        inviter = d[0][0]
        inviterUsername = "@deleted"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {inviter}")
        t = cur.fetchall()
        if len(t) > 0:
            inviterUsername = decode(t[0][0])
        if inviterUsername == "@deleted" or inviter < 0: # inviter < 0 => account banned
            return json.dumps({"success": False, "msg": "Invalid invitation code!"})

    inviteCode = genCode(8)

    userId = 1
    try:
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 1")
        t = cur.fetchall()
        if len(t) > 0:
            userId = t[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {userId + 1} WHERE type = 1")

        if len(username) > 500:
            return json.dumps({"success": False, "msg": "Username too long!"})
        if len(email) > 128:
            return json.dumps({"success": False, "msg": "Email too long!"})

        cur.execute(f"INSERT INTO UserInfo VALUES ({userId}, '{username}', '', '{email}', '{encode(password)}', {inviter}, '{inviteCode}')")
        conn.commit()
    except:
        sessions.errcnt += 1
        return json.dumps({"success": False, "msg": "Unknown error occured. Try again later..."})
    
    if userId == 1: # block default user and add the user to admin list
        cur.execute(f"UPDATE UserInfo SET email = 'disabled' WHERE userId = 0")
        cur.execute(f"UPDATE UserInfo SET inviteCode = '' WHERE userId = 0")
        cur.execute(f"INSERT INTO AdminList VALUES ({userId})")
        cur.execute(f"INSERT INTO UserNameTag VALUES ({userId}, '{encode('root')}', 'admin')")

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'register', {int(time.time())}, '{encode('Birth of account')}')")
    conn.commit()

    return json.dumps({"success": True, "msg": "You are registered! Now you can login!"})

@app.route("/api/user/login", methods = ['POST'])
def apiLogin():
    updateconn()
    cur = conn.cursor()
    username = encode(request.form["username"])
    password = request.form["password"]
    
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
        
    userId = d[0]

    if userId == 0:
        cur.execute(f"SELECT email FROM UserInfo WHERE userId = 0")
        t = cur.fetchall()
        if len(t) > 0:
            defaultemail = t[0][0]
            if defaultemail == "disabled":
                return json.dumps({"success": False, "msg": "Default user has been disabled!"})

    ip = encode(request.headers['CF-Connecting-Ip'])

    if sessions.getPasswordTrialCount(userId, ip)[0] >= 5 and int(time.time()) - sessions.getPasswordTrialCount(userId, ip)[1] <= 600:
        return json.dumps({"success": False, "msg": "Too many attempts! Try again later..."})

    if not checkpwd(password,decode(d[1])):
        if sessions.getPasswordTrialCount(userId, ip)[0] >= 5:
            sessions.updatePasswordTrialCount(userId, 3, time.time(), ip)
        else:
            sessions.updatePasswordTrialCount(userId, sessions.getPasswordTrialCount(userId, ip)[0] + 1, time.time(), ip)
            
        return json.dumps({"success": False, "msg": "Invalid password!"})
    
    sessions.updatePasswordTrialCount(userId, 0, 0, ip)

    cur.execute(f"SELECT * FROM RequestRecoverAccount WHERE userId = {userId}")
    t = cur.fetchall()

    if len(t) == 0:
        if sessions.checkDeletionMark(userId):
            cur.execute(f"INSERT INTO RequestRecoverAccount VALUES ({userId})")
            conn.commit()
            return json.dumps({"success": False, "msg": "Account marked for deletion, login again to recover it!"})
    else:
        cur.execute(f"DELETE FROM RequestRecoverAccount WHERE userId = {userId}")
        conn.commit()
        sessions.removeDeletionMark(userId)
    
    if userId < 0:
        return json.dumps({"success": False, "msg": "Account banned. Contact administrator for more information."})

    token = sessions.login(userId, encode(request.headers['User-Agent']), encode(request.headers['CF-Connecting-Ip']))

    isAdmin = False
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        isAdmin = True

    ip = request.headers["CF-Connecting-Ip"]
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'login', {int(time.time())}, '{encode(f'New login from {ip}')}')")
    conn.commit()

    return json.dumps({"success": True, "userId": userId, "token": token, "isAdmin": isAdmin})

@app.route("/api/user/logout", methods = ['POST'])
def apiLogout():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        return json.dumps({"success": True})

    userId = int(request.form["userId"])
    token = request.form["token"]
    ret = sessions.logout(userId, token)

    return json.dumps({"success": ret})

@app.route("/api/user/logoutalAll", methods = ['POST'])
def apiLogoutAll():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        return json.dumps({"success": True})

    userId = int(request.form["userId"])
    token = request.form["token"]
    ret = sessions.logoutAll(userId, token)

    return json.dumps({"success": ret})

@app.route("/api/user/delete", methods = ['POST'])
def apiDeleteAccount():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cur.execute(f"SELECT * FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        return json.dumps({"success": False, "msg": "Admins cannot delete their account on website! Contact super administrator for help!"})
    
    password = request.form["password"]
    cur.execute(f"SELECT password FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    pwdhash = d[0][0]
    if not checkpwd(password,decode(pwdhash)):
        return json.dumps({"success": False, "msg": "Invalid password!"})
    
    sessions.markDeletion(userId)

    ip = request.headers["CF-Connecting-Ip"]
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'delete_account', {int(time.time())}, '{encode(f'Account marked for deletion by {ip}')})")
    sessions.logout(userId, token)
    conn.commit()

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
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    d = None
    cur.execute(f"SELECT username, email, inviteCode, inviter, bio FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        d = t[0]
    else:
        return json.dumps({"success": False, "msg": "User not found!"})
    d = list(d)
    d[0] = decode(d[0])
    d[4] = decode(d[4])

    inviter = 0
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {d[3]}")
    t = cur.fetchall()
    if len(t) > 0:
        inviter = decode(t[0][0])

    regts = 0
    cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {userId} AND event = 'register'")
    t = cur.fetchall()
    if len(t) > 0:
        regts = t[0][0]
    age = math.ceil((time.time() - regts) / 86400)

    isAdmin = False
    cur.execute(f"SELECT * FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        isAdmin = True
        
    username = d[0]
    cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        username = f"<a href='/user?userId={userId}'><span style='color:{t[0][1]}'>{username}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"

    goal = 0
    cur.execute(f"SELECT count FROM UserGoal WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        goal = t[0][0]
    
    chtoday = 0
    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {userId} AND memorized = 1 AND timestamp >= {int(time.time()) - 86400}")
    t = cur.fetchall()
    if len(t) > 0:
        chtoday = t[0][0]
    
    checkin_today = False
    cur.execute(f"SELECT * FROM CheckIn WHERE userId = {userId} AND timestamp >= {int(int(time.time())/86400)*86400}") # utc 0:00
    t = cur.fetchall()
    if len(t) > 0:
        checkin_today = True
    
    checkin_continuous = 0
    cur.execute(f"SELECT timestamp FROM CheckIn WHERE userId = {userId} ORDER BY timestamp DESC")
    t = cur.fetchall()
    if len(t) > 0:
        lst = t[0][0]+86400
        for tt in t:
            if int(lst/86400) - int(tt[0]/86400) == 1:
                checkin_continuous += 1
                lst = tt[0]
            elif int(lst/86400) - int(tt[0]/86400) > 1:
                break

    return json.dumps({"username": username, "bio": d[4], "email": d[1], "invitationCode": d[2], "inviter": inviter, "age": age, "isAdmin": isAdmin, \
        "goal": goal, "chtoday": chtoday, "checkin_today": checkin_today, "checkin_continuous": checkin_continuous})

@app.route("/api/user/goal", methods = ['POST'])
def apiGetUserGoal():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    goal = 0
    cur.execute(f"SELECT count FROM UserGoal WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        goal = t[0][0]
    
    chtoday = 0
    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {userId} AND memorized = 1 AND timestamp >= {int(time.time()) - 86400}")
    t = cur.fetchall()
    if len(t) > 0:
        chtoday = t[0][0]
    
    checkin_today = False
    cur.execute(f"SELECT * FROM CheckIn WHERE userId = {userId} AND timestamp >= {int(int(time.time())/86400)*86400}") # utc 0:00
    t = cur.fetchall()
    if len(t) > 0:
        checkin_today = True
    
    checkin_continuous = 0
    cur.execute(f"SELECT timestamp FROM CheckIn WHERE userId = {userId} ORDER BY timestamp DESC")
    t = cur.fetchall()
    if len(t) > 0:
        lst = t[0][0]+86400
        for tt in t:
            if int(lst/86400) - int(tt[0]/86400) == 1:
                checkin_continuous += 1
                lst = tt[0]
            elif int(lst/86400) - int(tt[0]/86400) > 1:
                break
    
    return json.dumps({"goal": goal, "chtoday": chtoday, "checkin_today": checkin_today, "checkin_continuous": checkin_continuous})

@app.route("/api/user/updateGoal", methods = ['POST'])
def apiUserUpdateGoal():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    goal = int(request.form["goal"])
    cur.execute(f"SELECT * FROM UserGoal WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        cur.execute(f"INSERT INTO UserGoal VALUES ({userId}, {goal})")
    else:
        cur.execute(f"UPDATE UserGoal SET count = {goal} WHERE userId = {userId}")
    conn.commit()

    return json.dumps({"success": True, "msg": "Goal updated!"})

@app.route("/api/user/checkin", methods = ['POST'])
def apiUserCheckin():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cur.execute(f"SELECT * FROM CheckIn WHERE userId = {userId} AND timestamp >= {int(time.time()/86400)*86400}")
    if len(cur.fetchall()) > 0:
        return json.dumps({"success": False, "msg": "You have already checked in today!"})
    
    goal = 0
    cur.execute(f"SELECT count FROM UserGoal WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        goal = t[0][0]

    if goal == 0:
        return json.dumps({"success": False, "msg": "Have a goal first!"})
    
    chtoday = 0
    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {userId} AND memorized = 1 AND timestamp >= {int(time.time()) - 86400}")
    t = cur.fetchall()
    if len(t) > 0:
        chtoday = t[0][0]

    if chtoday < goal:
        return json.dumps({"success": False, "msg": "You haven't accomplished today's goal!"})
        
    cur.execute(f"INSERT INTO CheckIn VALUES ({userId}, {int(time.time())})")
    conn.commit()

    return json.dumps({"success": True, "msg": "Checked in successfully!"})

@app.route("/api/user/chart/<int:uid>", methods = ['GET'])
def apiGetUserChart(uid):
    updateconn()
    cur = conn.cursor()
    
    cur.execute(f"SELECT * FROM UserInfo WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) == 0:
        return json.dumps({"success": False, "msg": "User not found!"})
    
    d1 = []
    batch = 3
    for i in range(30):
        cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {uid} AND memorized = 1 AND timestamp >= {int(time.time()) - 86400*batch*(i+1)} AND timestamp <= {int(time.time()) - 86400*batch*i}")
        t = cur.fetchall()
        memorized = 0
        if len(t) > 0:
            memorized = t[0][0]

        cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {uid} AND memorized = 0 AND timestamp >= {int(time.time()) - 86400*batch*(i+1)} AND timestamp <= {int(time.time()) - 86400*batch*i}")
        t = cur.fetchall()
        forgotten = 0
        if len(t) > 0:
            forgotten = t[0][0]
        
        d1.append({"index": 30 - i, "memorized": memorized, "forgotten": forgotten})
    
    d2 = []
    total_memorized = 0
    batch = 3
    for i in range(30):
        cur.execute(f"SELECT COUNT(*) FROM MyMemorized WHERE userId = {uid} AND timestamp <= {int(time.time()) - 86400*batch*i}")
        t = cur.fetchall()
        total = 0
        if len(t) > 0:
            total = t[0][0]
        total_memorized = total
        d2.append({"index": 30 - i, "total": total})
    
    cnt = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) > 0:
        cnt = t[0][0]

    tagcnt = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {uid} AND status = 2")
    t = cur.fetchall()
    if len(t) > 0:
        tagcnt = t[0][0]

    delcnt = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {uid} AND status = 3")
    t = cur.fetchall()
    if len(t) > 0:
        delcnt = t[0][0]

    return json.dumps({"challenge_history": d1, "total_memorized_history": d2, "tag_cnt": tagcnt, "del_cnt": delcnt, "total_memorized": total_memorized, "total": cnt})

@app.route("/api/user/publicInfo/<int:uid>", methods = ['GET'])
def apiGetUserPublicInfo(uid):
    updateconn()
    cur = conn.cursor()
    
    cur.execute(f"SELECT username, bio FROM UserInfo WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) == 0:
        return json.dumps({"success": False, "msg": "User not found!"})
    username = decode(t[0][0])
    bio = decode(t[0][1])
    
    cnt = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) > 0:
        cnt = t[0][0]

    tagcnt = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {uid} AND status = 2")
    t = cur.fetchall()
    if len(t) > 0:
        tagcnt = t[0][0]

    delcnt = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {uid} AND status = 3")
    t = cur.fetchall()
    if len(t) > 0:
        delcnt = t[0][0]

    chcnt = 0
    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) > 0:
        chcnt = t[0][0]

    regts = 0
    cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {uid} AND event = 'register'")
    t = cur.fetchall()
    if len(t) > 0:
        regts = t[0][0]
    age = math.ceil((time.time() - regts) / 86400)

    isAdmin = False
    cur.execute(f"SELECT * FROM AdminList WHERE userId = {uid}")
    if len(cur.fetchall()) != 0:
        isAdmin = True

    cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) > 0:
        username = f"<a href='/user?userId={uid}'><span style='color:{t[0][1]}'>{username}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"

    return json.dumps({"username": username, "bio": bio, "cnt": cnt, "tagcnt": tagcnt, "delcnt": delcnt, "chcnt": chcnt, "age": age, "isAdmin": isAdmin})   

@app.route("/api/user/events", methods = ['POST'])
def apiUserEvents():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cur.execute(f"SELECT timestamp, msg FROM UserEvent WHERE userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()
    ret = []
    for dd in d:
        ret.append({"timestamp": dd[0], "msg": decode(dd[1])})
    
    return json.dumps(ret)

@app.route("/api/user/sessions", methods=['POST'])
def apiUserSessions():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ss = []
    cur.execute(f"SELECT loginTime, expireTime, ua, ip, token FROM ActiveUserLogin WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        if dd[1] <= int(time.time()):
            cur.execute(f"DELETE FROM ActiveUserLogin WHERE token = '{dd[4]}' AND userId = {userId}")
        else:
            ss.append({"loginTime": dd[0], "expireTime": dd[1], "userAgent": decode(dd[2]), "ip": decode(dd[3])})
    
    return json.dumps(ss)

@app.route("/api/user/updateInfo", methods=['POST'])
def apiUpdateInfo():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    username = request.form["username"]
    email = request.form["email"]
    bio = request.form["bio"]

    if username is None or email is None\
        or username.replace(" ","") == "" or email.replace(" ","") == "":
        return json.dumps({"success": False, "msg": "All the fields must be filled!"})
    if " " in username or "(" in username or ")" in username or "[" in username or "]" in username or "{" in username or "}" in username \
        or "<" in username or ">" in username \
            or "!" in username or "@" in username or "'" in username or '"' in username or "/" in username or "\\" in username :
        return json.dumps({"success": False, "msg": "Username must not contain: spaces, ( ) [ ] { } < > ! @ ' \" / \\"})
    username = encode(username)
    if validators.email(email) != True:
        return json.dumps({"success": False, "msg": "Invalid email!"})
    bio = encode(bio)
    
    cur.execute(f"SELECT * FROM UserInfo WHERE username = '{username}' AND userId != {userId}")
    if len(cur.fetchall()) != 0:
        return json.dumps({"success": False, "msg": "Username occupied!"})
    
    if len(encode(username)) > 500:
        return json.dumps({"success": False, "msg": "Username too long!"})
    if len(encode(bio)) > 1000:
        return json.dumps({"success": False, "msg": "Bio too long!"})
    if len(encode(email)) > 100:
        return json.dumps({"success": False, "msg": "Email too long!"})

    cur.execute(f"UPDATE UserInfo SET username = '{username}' WHERE userId = {userId}")
    cur.execute(f"UPDATE UserInfo SET bio = '{bio}' WHERE userId = {userId}")
    cur.execute(f"UPDATE UserInfo SET email = '{email}' WHERE userId = {userId}")
    conn.commit()

    return json.dumps({"success": True, "msg": "User profile updated!"})

@app.route("/api/user/changepassword", methods=['POST'])
def apiChangePassword():
    updateconn()
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
    
    pwd = ""
    cur.execute(f"SELECT password FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        pwd = t[0][0]
    if not checkpwd(oldpwd, decode(pwd)):
        return json.dumps({"success": False, "msg": "Incorrect old password!"})

    if newpwd != cfmpwd:
        return json.dumps({"success": False, "msg": "New password and confirm password mismatch!"})

    newhashed = hashpwd(newpwd)
    cur.execute(f"UPDATE UserInfo SET password = '{encode(newhashed)}' WHERE userId = {userId}")
    
    ip = request.headers["CF-Connecting-Ip"]
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'change_password', {int(time.time())}, '{encode(f'Password changed by {ip}')}')")
    sessions.logoutAll(userId)
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/user/settings", methods = ['POST'])
def apiUserSettings():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    op = request.form["operation"]

    if op == "upload":    
        rnd = int(request.form["random"])
        swp = int(request.form["swap"])
        showStatus = int(request.form["showStatus"])
        mode = int(request.form["mode"])
        ap = int(request.form["autoPlay"])
        theme = request.form["theme"]
        if not theme in ["light","dark"]:
            return json.dumps({"success": False, "msg": "Theme can only be light or dark"})

        cur.execute(f"DELETE FROM UserSettings WHERE userId = {userId}")
        cur.execute(f"INSERT INTO UserSettings VALUES ({userId}, {rnd}, {swp}, {showStatus}, {mode}, {ap}, '{theme}')")
        conn.commit()

        return json.dumps({"success": True, "msg": "Settings synced!"})
    
    elif op == "download":
        rnd = 0
        swp = 0
        showStatus = 1
        mode = 0
        autoPlay = 0
        theme = 'light'

        cur.execute(f"SELECT * FROM UserSettings WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) > 0:
            rnd = d[0][1]
            swp = d[0][2]
            showStatus = d[0][3]
            mode = d[0][4]
            autoPlay = d[0][5]
            theme = d[0][6]
                
        return json.dumps({"success": True, "msg": "Settings synced!", "random": rnd, "swap": swp, "showStatus": showStatus,\
            "mode": mode, "autoPlay": autoPlay, "theme": theme})