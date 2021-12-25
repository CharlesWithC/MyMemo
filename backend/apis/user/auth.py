# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks
import os, sys, time, math, uuid
import json
import validators

from app import app, config
from db import newconn
from functions import *
import sessions
from emailop import sendVerification, sendNormal

##########
# User Auth API

requestRecoverAccount = []

@app.post("/api/user/login")
async def apiLogin(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()

    captchaToken = form["captchaToken"]
    captchaAnswer = form["captchaAnswer"]
    captchaResult = validateCaptcha(captchaToken, captchaAnswer)
    if captchaResult != True:
        return captchaResult

    username = encode(form["username"])
    password = form["password"]

    cur.execute(f"DELETE FROM UserPending WHERE expire <= {int(time.time())}")
    conn.commit()

    cur.execute(f"SELECT puserId, password FROM UserPending WHERE username = '{username}'")
    t = cur.fetchall()
    if len(t) > 0:
        puserId = t[0][0]
        
        # use negative userId for password trial count
        if sessions.getPasswordTrialCount(-puserId, ip)[0] >= 5 and int(time.time()) - sessions.getPasswordTrialCount(-puserId, ip)[1] <= 600:
            return {"success": False, "msg": "Too many attempts! Try again later..."}

        if not checkpwd(password, decode(t[0][1])):
            if sessions.getPasswordTrialCount(-puserId, ip)[0] >= 5:
                sessions.updatePasswordTrialCount(-puserId, 3, time.time(), ip)
            else:
                sessions.updatePasswordTrialCount(-puserId, sessions.getPasswordTrialCount(-puserId, ip)[0] + 1, time.time(), ip)
                
            return {"success": False, "msg": "Incorrect username or password!"}

        sessions.updatePasswordTrialCount(-puserId, 0, 0, ip)

        ptoken = b62encode(int(time.time())) + "-" + str(uuid.uuid4())
        loginTime = int(time.time())
        expireTime = loginTime + 1800 # 30 minutes
        cur.execute(f"INSERT INTO UserPendingToken VALUES ({puserId}, '{ptoken}')")
        conn.commit()

        return {"success": True, "active": False, "puserId": puserId, "ptoken": ptoken}
    
    d = [-1]
    try:
        cur.execute(f"SELECT userId, password FROM UserInfo WHERE username = '{username}'")
        d = cur.fetchall()
        if len(d) == 0:
            username = decode(username)
            if validators.email(username) == True:
                cur.execute(f"SELECT userId, password FROM UserInfo WHERE email = '{encode(username)}'")
                d = cur.fetchall()
                if len(d) == 0:
                    return {"success": False, "msg": "Incorrect username or password!"}
            else:
                return {"success": False, "msg": "Incorrect username or password!"}
        d = d[0]
    except:
        sessions.errcnt += 1
        return {"success": False, "msg": "Unknown error occured. Try again later..."}
        
    userId = d[0]

    if userId == 0:
        cur.execute(f"SELECT email FROM UserInfo WHERE userId = 0")
        t = cur.fetchall()
        if len(t) > 0:
            defaultemail = t[0][0]
            if defaultemail == "disabled":
                return {"success": False, "msg": "Default user has been disabled!"}

    if sessions.getPasswordTrialCount(userId, ip)[0] >= 5 and int(time.time()) - sessions.getPasswordTrialCount(userId, ip)[1] <= 600:
        return {"success": False, "msg": "Too many attempts! Try again later..."}

    if not checkpwd(password,decode(d[1])):
        if sessions.getPasswordTrialCount(userId, ip)[0] >= 5:
            sessions.updatePasswordTrialCount(userId, 3, time.time(), ip)
        else:
            sessions.updatePasswordTrialCount(userId, sessions.getPasswordTrialCount(userId, ip)[0] + 1, time.time(), ip)
            
        return {"success": False, "msg": "Incorrect username or password!"}
    
    sessions.updatePasswordTrialCount(userId, 0, 0, ip)

    global requestRecoverAccount
    if not userId in requestRecoverAccount:
        if sessions.checkDeletionMark(userId):
            requestRecoverAccount.append(userId)
            return {"success": False, "msg": "Account marked for deletion, login again to recover it!"}
    else:
        requestRecoverAccount.remove(userId)
        sessions.removeDeletionMark(userId)
    
    if userId < 0:
        reason = ""
        cur.execute(f"SELECT reason FROM BanReason WHERE userId = {-userId}")
        t = cur.fetchall()
        if len(t) > 0:
            reason = "Reason: " + decode(t[0][0])
        return {"success": False, "msg": "Account banned. " + reason}

    token = sessions.login(userId, encode(request.headers['User-Agent']), ip)

    isAdmin = False
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        isAdmin = True

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'login', {int(time.time())}, '{encode(f'New login from {ip}')}')")
    conn.commit()
    
    cur.execute(f"SELECT username, email FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    username = decode(t[0][0])
    email = decode(t[0][1])
    background_tasks.add_task(sendNormal, email, username, f"New login from {ip}", f"A new login has been detected.<br>IP: {ip}<br>If this isn't you, reset your password immediately!")

    return {"success": True, "active": True, "userId": userId, "token": token, "isAdmin": isAdmin}

@app.post("/api/user/logout")
async def apiLogout(request: Request):
    ip = request.client.host
    form = await request.form()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        return {"success": True}

    userId = int(form["userId"])
    token = form["token"]
    ret = sessions.logout(userId, token)

    return {"success": ret}

@app.post("/api/user/logoutalAll")
async def apiLogoutAll(request: Request):
    ip = request.client.host
    form = await request.form()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        return {"success": True}

    userId = int(form["userId"])
    token = form["token"]
    ret = sessions.logoutAll(userId, token)

    return {"success": ret}

@app.post("/api/user/validate")
async def apiValidateToken(request: Request):
    ip = request.client.host
    form = await request.form()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        return {"success": True, "validation": False}
    userId = int(form["userId"])
    token = form["token"]
    return {"success": True, "validation": validateToken(userId, token)}

@app.post("/api/user/requestResetPassword")
async def apiRequestResetPassword(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    email = form["email"]

    cur.execute(f"DELETE FROM EmailVerification WHERE operation = 'reset_password' AND expire <= {int(time.time()) - 600}")
    conn.commit()

    cur.execute(f"SELECT userId, username FROM UserInfo WHERE email = '{encode(email)}'")
    d = cur.fetchall()
    if len(d) != 0:
        userId = d[0][0]

        cur.execute(f"SELECT expire FROM EmailVerification WHERE operation = 'reset_password' AND userId = {userId}")
        t = cur.fetchall()
        if len(t) > 0:
            return {"success": True, "msg": "An email containing password reset link will be sent if there is an user registered with this email! Check your spam folder if you didn't receive it."}

    if validators.email(email) == True:
        cur.execute(f"SELECT userId, username FROM UserInfo WHERE email = '{encode(email)}'")
        d = cur.fetchall()
        if len(d) != 0:
            userId = d[0][0]
            username = d[0][1]

            if OPLimit(userId, "reset_password", maxop = 1):
                return {"success": False, "msg": "Too many requests! Try again later!"}
            
            token = b62encode(int(time.time())) + "-" + str(uuid.uuid4())
            background_tasks.add_task(sendVerification, email, decode(username), "Password recovery", \
                f"You are recovering your password. Open the link below to continue!<br>If you didn't request that, simply ignore this email and your account will be safe.", "10 minutes", \
                    "https://memo.charles14.xyz/user/reset?token="+token)
            cur.execute(f"INSERT INTO EmailVerification VALUES ({userId}, 'reset_password', '{token}', {int(time.time()+600)})")
            conn.commit()
            
        return {"success": True, "msg": "An email containing password reset link will be sent if there is an user registered with this email! Check your spam folder if you didn't receive it."}

    else:
        return {"success": False, "msg": "Incorrect email address!"}

@app.post("/api/user/resetPassword")
async def apiResetPassword(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    token = form['token']
    
    cur.execute(f"DELETE FROM EmailVerification WHERE operation = 'reset_password' AND expire <= {int(time.time()) - 600}")
    conn.commit()

    token = form["token"]
    token = token
    
    if token == "" or not token.replace("-","").replace("_","").isalnum():
        return {"success": False, "msg": "Invalid or expired verification token!"}

    cur.execute(f"SELECT userId FROM EmailVerification WHERE operation = 'reset_password' AND token = '{token}'")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Invalid or expired verification token!"}
    
    if 'validate' in form.keys():
        return {"success": True}

    userId = t[0][0]

    newpwd = form['newpwd']

    newhashed = hashpwd(newpwd)

    cur.execute(f"DELETE FROM EmailVerification WHERE operation = 'reset_password' AND token = '{token}'")
    cur.execute(f"UPDATE UserInfo SET password = '{encode(newhashed)}' WHERE userId = {userId}")
    conn.commit()

    cur.execute(f"SELECT username, email FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    username = decode(t[0][0])
    email = decode(t[0][1])

    background_tasks.add_task(sendNormal, email, username, "Password updated", f"Your password has been updated. If you didn't do this, reset your password immediately!")
    
    return {"success": True, "msg": "Password updated!"}