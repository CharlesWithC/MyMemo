# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time, math
import json
import validators
import sqlite3

from app import app, config
from functions import *
import sessions





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
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 1")
        userId = cur.fetchall()[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {userId + 1} WHERE type = 1")

        cur.execute(f"INSERT INTO UserInfo VALUES ({userId}, '{username}', '{email}', '{encode(password)}', {inviter}, '{inviteCode}')")
        conn.commit()
    except:
        sessions.errcnt += 1
        return json.dumps({"success": False, "msg": "Unknown error occured. Try again later..."})

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'register', {int(time.time())})")
    conn.commit()

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

@app.route("/api/user/delete", methods = ['POST'])
def apiDeleteAccount():
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

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'delete_account', {int(time.time())})")
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

    isAdmin = False
    cur.execute(f"SELECT * FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        isAdmin = True

    return json.dumps({"username": d[0], "email": d[1], "invitationCode": d[2], "inviter": inviter, "cnt": cnt, "tagcnt": tagcnt, "delcnt": delcnt, "chcnt": chcnt, "age": age, "isAdmin": isAdmin})

@app.route("/api/user/updateInfo", methods=['POST'])
def apiUpdateInfo():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    username = request.form["username"]
    email = request.form["email"]

    if username is None or email is None\
        or username.replace(" ","") == "" or email.replace(" ","") == "":
        return json.dumps({"success": False, "msg": "All the fields must be filled!"})
    if not username.replace("_","").isalnum():
        return json.dumps({"success": False, "msg": "Username can only contain alphabets, digits and underscore!"})
    if validators.email(email) != True:
        return json.dumps({"success": False, "msg": "Invalid email!"})
    
    cur.execute(f"SELECT * FROM UserInfo WHERE username = '{username}' AND userId != {userId}")
    if len(cur.fetchall()) != 0:
        return json.dumps({"success": False, "msg": "Username occupied!"})
    
    cur.execute(f"UPDATE UserInfo SET username = '{username}' WHERE userId = {userId}")
    cur.execute(f"UPDATE UserInfo SET email = '{email}' WHERE userId = {userId}")
    conn.commit()

    return json.dumps({"success": True, "msg": "User profile updated!"})

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
    conn.commit()

    return json.dumps({"success": True})