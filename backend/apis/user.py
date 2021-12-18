# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks
import os, sys, time, math, uuid
import threading
import json
import validators

from app import app, config
from db import newconn
from functions import *
import sessions
from emailop import sendVerification, sendNormal

##########
# User API

@app.post("/api/user/register")
async def apiRegister(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    if not config.allow_register:
        return {"success": False, "msg": "Public register not enabled!"}
        
    conn = newconn()
    cur = conn.cursor()

    userCnt = 0
    cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId > 0") # banned users are not counted
    t = cur.fetchall()
    if len(t) > 0:
        userCnt = t[0][0]
    if config.max_user_allowed != -1 and userCnt >= config.max_user_allowed:
        return {"success": False, "msg": "System has reached its limit of maximum registered users. Contact administrator for more information."}

    username = form["username"]
    email = form["email"]
    password = form["password"]
    invitationCode = form["invitationCode"]

    if username is None or email is None or password is None \
        or username.replace(" ","") == "" or email.replace(" ","") == "" or password.replace(" ","") == "":
        return {"success": False, "msg": "Username and email must be filled!"}
    if " " in username or "(" in username or ")" in username or "[" in username or "]" in username or "{" in username or "}" in username \
        or "<" in username or ">" in username \
            or "!" in username or "@" in username or "'" in username or '"' in username or "/" in username or "\\" in username :
        return {"success": False, "msg": "Username must not contain: spaces, ( ) [ ] { } < > ! @ ' \" / \\"}
    username = encode(username)
    if validators.email(email) != True or "'" in email or '"' in email:
        return {"success": False, "msg": "Invalid email!"}
    if invitationCode != "" and not invitationCode.isalnum():
        return {"success": False, "msg": "Invitation code can only contain alphabets and digits!"}
    
    cur.execute(f"DELETE FROM UserPending WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT username, email FROM UserPending")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if tt[1].lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    cur.execute(f"DELETE FROM PendingEmailChange WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT email FROM PendingEmailChange")
    t = cur.fetchall()
    for tt in t:
        if tt[0].lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}
        elif tt[0].startswith("!") and tt[0].lower()[1:] == email.lower():
            return {"success": False, "msg": "The previous owner of this email has updated their email within 7 days so this email address is reserved for 7 days!"}

    cur.execute(f"SELECT username, email FROM UserInfo")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if tt[1].lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    password = hashpwd(password)
    
    inviter = 0
    if config.use_invite_system:
        cur.execute(f"SELECT userId FROM UserInfo WHERE inviteCode = '{invitationCode}'")
        d = cur.fetchall()
        if len(d) == 0:
            return {"success": False, "msg": "Invalid invitation code!"}
        inviter = d[0][0]
        inviterUsername = "@deleted"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {inviter}")
        t = cur.fetchall()
        if len(t) > 0:
            inviterUsername = decode(t[0][0])
        if inviterUsername == "@deleted" or inviter < 0: # inviter < 0 => account banned
            return {"success": False, "msg": "Invalid invitation code!"}
    
    if len(username) >= 256:
        return {"success": False, "msg": "Username too long!"}
    if len(email) >= 128:
        return {"success": False, "msg": "Email too long!"}

    if OPLimit(request.headers['CF-Connecting-Ip'], "register", maxop = 1):
        return {"success": False, "msg": "Too many requests! You can only register one account with one ip each 5 minutes!"}

    token = str(uuid.uuid4())
    background_tasks.add_task(sendVerification, email, decode(username), "Account activation", \
        f"Welcome {decode(username)}! Please verify your email to activate your account!", "3 hours", \
            "https://memo.charles14.xyz/user/activate?token="+token)
    
    puserId = 1
    try:
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 0")
        t = cur.fetchall()
        if len(t) > 0:
            puserId = t[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {puserId + 1} WHERE type = 0")

        cur.execute(f"INSERT INTO UserPending VALUES ({puserId}, '{username}', '{email}', '{encode(password)}', {inviter}, '{token}', {int(time.time() + 3600 * 3)})")
        conn.commit()
    except:
        sessions.errcnt += 1
        return {"success": False, "msg": "Unknown error occured. Try again later..."}

    return {"success": True, "msg": "Account registered, but pending activation! \
        Check your email and open the verification link to activate your account! \
        The link expires in 3 hours. After that your account will be removed and you need to register again!"}

@app.post("/api/user/activate")
async def apiActivate(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()

    token = form["token"]
    token = token
    if token == "" or not token.replace("-","").replace("_","").isalnum():
        return {"success": False, "msg": "Invalid or expired activation token!"}

    cur.execute(f"SELECT username, email, password, inviter, expire FROM UserPending WHERE token = '{token}'")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Invalid or expired activation token!"}
    
    if t[0][4] <= int(time.time()):
        cur.execute(f"DELETE FROM UserPending WHERE token = '{token}'")
        conn.commit()
        return {"success": False, "msg": "Activation token expired! Please register again!"}
    
    username = t[0][0]
    email = t[0][1]
    password = t[0][2]
    inviter = t[0][3]

    inviteCode = genCode(8)

    userId = 1
    try:
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 1")
        t = cur.fetchall()
        if len(t) > 0:
            userId = t[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {userId + 1} WHERE type = 1")

        cur.execute(f"INSERT INTO UserInfo VALUES ({userId}, '{username}', '', '{email}', '{password}', {inviter}, '{inviteCode}', 99999)")
        conn.commit()
    except:
        sessions.errcnt += 1
        return {"success": False, "msg": "Unknown error occured. Try again later..."}

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'register', {int(time.time())}, '{encode('Birth of account')}')")
    
    if userId == 1: # block default user and add the user to admin list
        cur.execute(f"UPDATE UserInfo SET email = 'disabled' WHERE userId = 0")
        cur.execute(f"UPDATE UserInfo SET inviteCode = '' WHERE userId = 0")
        cur.execute(f"INSERT INTO AdminList VALUES ({userId})")
        cur.execute(f"INSERT INTO UserNameTag VALUES ({userId}, '{encode('root')}', 'purple')")
    
    cur.execute(f"DELETE FROM UserPending WHERE token = '{token}'")
    cur.execute(f"INSERT INTO EmailHistory VALUES ({userId}, '{email}', {int(time.time())})")
    conn.commit()

    return {"success": True, "msg": "Account activated!"}

@app.post("/api/user/pending/getInfo")
async def apiUserPendingGetInfo(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    puserId = int(form["puserId"])
    ptoken = form["ptoken"]

    if not ptoken.replace("-","").isalnum():
        return {"success": False, "msg": "Invalid token!"}
    
    cur.execute(f"SELECT puserId FROM UserPendingToken WHERE puserId = {puserId} AND token = '{ptoken}'")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Session expired!"}

    cur.execute(f"SELECT username, email FROM UserPending WHERE puserId = {puserId}")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Invalid token!"}
    username = decode(t[0][0])
    email = t[0][1]

    return {"success": True, "username": username, "email": email}

@app.post("/api/user/pending/updateInfo")
async def apiUserPendingUpdateInfo(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    puserId = int(form["puserId"])
    ptoken = form["ptoken"]

    if not ptoken.replace("-","").isalnum():
        return {"success": False, "msg": "Invalid token!"}
    
    cur.execute(f"SELECT puserId FROM UserPendingToken WHERE puserId = {puserId} AND token = '{ptoken}'")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Session expired!"}

    username = form["username"]
    email = form["email"]

    if username is None or email is None\
        or username.replace(" ","") == "" or email.replace(" ","") == "":
        return {"success": False, "msg": "Username and email must be filled!"}
    if " " in username or "(" in username or ")" in username or "[" in username or "]" in username or "{" in username or "}" in username \
        or "<" in username or ">" in username \
            or "!" in username or "@" in username or "'" in username or '"' in username or "/" in username or "\\" in username :
        return {"success": False, "msg": "Username must not contain: spaces, ( ) [ ] { } < > ! @ ' \" / \\"}
    username = encode(username)
    if validators.email(email) != True or "'" in email or '"' in email:
        return {"success": False, "msg": "Invalid email!"}

    cur.execute(f"SELECT username, email FROM UserPending WHERE puserId != {puserId}")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if tt[1].lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    cur.execute(f"DELETE FROM PendingEmailChange WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT email FROM PendingEmailChange")
    t = cur.fetchall()
    for tt in t:
        if tt[0].lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}
        elif tt[0].startswith("!") and tt[0].lower()[1:] == email.lower():
            return {"success": False, "msg": "The previous owner of this email has updated their email within 7 days so this email address is reserved for 7 days!"}

    cur.execute(f"SELECT username, email FROM UserInfo")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if tt[1].lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    cur.execute(f"UPDATE UserPending SET username = '{username}' WHERE puserId = {puserId}")
    cur.execute(f"UPDATE UserPending SET email = '{email}' WHERE puserId = {puserId}")
    conn.commit()

    resend = int(form["resend"])

    if resend:
        if OPLimit(puserId, "resend_activation", maxop = 2):
            return {"success": False, "msg": "Too many requests! Try again later!"}

        cur.execute(f"SELECT token FROM UserPending WHERE puserId = {puserId}")
        t = cur.fetchall()
        token = t[0][0]
        background_tasks.add_task(sendVerification, email, decode(username), "Account activation", \
            f"Welcome {decode(username)}! Please verify your email to activate your account!", "3 hours", \
                "https://memo.charles14.xyz/user/activate?token="+token)
        return {"success": True, "msg": "A new activation email has been sent! Please check your inbox and open the link to activate your account!"}

    return {"success": True, "msg": "User information updated!"}

@app.post("/api/user/login")
async def apiLogin(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    username = encode(form["username"])
    password = form["password"]

    cur.execute(f"DELETE FROM UserPending WHERE expire <= {int(time.time())}")
    conn.commit()

    ip = encode(request.headers['CF-Connecting-Ip'])

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
            if validators.email(username) == True and not "'" in username:
                cur.execute(f"SELECT userId, password FROM UserInfo WHERE email = '{username}'")
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

    ip = encode(request.headers['CF-Connecting-Ip'])

    if sessions.getPasswordTrialCount(userId, ip)[0] >= 5 and int(time.time()) - sessions.getPasswordTrialCount(userId, ip)[1] <= 600:
        return {"success": False, "msg": "Too many attempts! Try again later..."}

    if not checkpwd(password,decode(d[1])):
        if sessions.getPasswordTrialCount(userId, ip)[0] >= 5:
            sessions.updatePasswordTrialCount(userId, 3, time.time(), ip)
        else:
            sessions.updatePasswordTrialCount(userId, sessions.getPasswordTrialCount(userId, ip)[0] + 1, time.time(), ip)
            
        return {"success": False, "msg": "Incorrect username or password!"}
    
    sessions.updatePasswordTrialCount(userId, 0, 0, ip)

    cur.execute(f"SELECT * FROM RequestRecoverAccount WHERE userId = {userId}")
    t = cur.fetchall()

    if len(t) == 0:
        if sessions.checkDeletionMark(userId):
            cur.execute(f"INSERT INTO RequestRecoverAccount VALUES ({userId})")
            conn.commit()
            return {"success": False, "msg": "Account marked for deletion, login again to recover it!"}
    else:
        cur.execute(f"DELETE FROM RequestRecoverAccount WHERE userId = {userId}")
        conn.commit()
        sessions.removeDeletionMark(userId)
    
    if userId < 0:
        reason = ""
        cur.execute(f"SELECT reason FROM BanReason WHERE userId = {-userId}")
        t = cur.fetchall()
        if len(t) > 0:
            reason = "Reason: " + decode(t[0][0])
        return {"success": False, "msg": "Account banned. " + reason}

    token = sessions.login(userId, encode(request.headers['User-Agent']), encode(request.headers['CF-Connecting-Ip']))

    isAdmin = False
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        isAdmin = True

    ip = request.headers["CF-Connecting-Ip"]
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'login', {int(time.time())}, '{encode(f'New login from {ip}')}')")
    conn.commit()
    
    cur.execute(f"SELECT username, email FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    username = decode(t[0][0])
    email = t[0][1]
    background_tasks.add_task(sendNormal, email, username, f"New login from {ip}", f"A new login has been detected.<br>IP: {ip}<br>If this isn't you, reset your password immediately!")

    return {"success": True, "active": True, "userId": userId, "token": token, "isAdmin": isAdmin}

@app.post("/api/user/logout")
async def apiLogout(request: Request):
    form = await request.form()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        return {"success": True}

    userId = int(form["userId"])
    token = form["token"]
    ret = sessions.logout(userId, token)

    return {"success": ret}

@app.post("/api/user/logoutalAll")
async def apiLogoutAll(request: Request):
    form = await request.form()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        return {"success": True}

    userId = int(form["userId"])
    token = form["token"]
    ret = sessions.logoutAll(userId, token)

    return {"success": ret}

@app.post("/api/user/requestResetPassword")
async def apiRequestResetPassword(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    email = form["email"]

    cur.execute(f"DELETE FROM EmailVerification WHERE operation = 'reset_password' AND expire <= {int(time.time()) - 600}")
    conn.commit()

    cur.execute(f"SELECT userId, username FROM UserInfo WHERE email = '{email}'")
    d = cur.fetchall()
    if len(d) != 0:
        userId = d[0][0]

        cur.execute(f"SELECT expire FROM EmailVerification WHERE operation = 'reset_password' AND userId = {userId}")
        t = cur.fetchall()
        if len(t) > 0:
            return {"success": True, "msg": "An email containing password reset link will be sent if there is an user registered with this email! Check your spam folder if you didn't receive it."}

    if validators.email(email) == True:
        cur.execute(f"SELECT userId, username FROM UserInfo WHERE email = '{email}'")
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
    email = t[0][1]

    background_tasks.add_task(sendNormal, email, username, "Password updated", f"Your password has been updated. If you didn't do this, reset your password immediately!")
    
    return {"success": True, "msg": "Password updated!"}

@app.post("/api/user/requestDelete")
async def apiRequestDeleteAccount(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    cur.execute(f"SELECT * FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) != 0:
        return {"success": False, "msg": "Admins cannot delete their account on website! Contact super administrator for help!"}
    
    password = form["password"]
    cur.execute(f"SELECT password FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    pwdhash = d[0][0]
    if not checkpwd(password,decode(pwdhash)):
        return {"success": False, "msg": "Invalid password!"}
    
    cur.execute(f"SELECT username, email FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0:
        username = d[0][0]
        email = d[0][1]
        
        if OPLimit(userId, "delete_account", maxop = 1):
            return {"success": False, "msg": "Too many requests! Try again later!"}
            
        token = b62encode(int(time.time())) + "-" + str(uuid.uuid4())
        background_tasks.add_task(sendVerification, email, decode(username), "Account deletion", \
            f"It's sad to see you leave, open the link below to continue deleting your account.<br>\n\
                Your account will be marked for deletion and it will be deleted after 14 days.<br>\n\
                You can recover it by logging in at any time during that period.<br>\n\
                After 14 days it will be deleted permanently and cannot be recovered.<br>\n\
                <br>\n\
                Deleting your account will make you unable to login permanently but all your other data will be preserved.<br>\n\
                You can delete most of the data manually such as questions and books, and Discovery posts.<br>\n\
                If you want a deep data wipe, you can contact administrator and provide your User ID: {userId}.<br>\n\
                Administrators will be able to wipe your data completely after your account is deleted.<br>\n\
                <br>\n\
                If you didn't request the deletion, reset your password immediately!", "10 minutes", \
                "https://memo.charles14.xyz/user/delete?token="+token)
        cur.execute(f"INSERT INTO EmailVerification VALUES ({userId}, 'delete_account', '{token}', {int(time.time()+600)})")
        conn.commit()
        
    return {"success": True, "msg": "An email containing confirmation link has been sent. Open the link to continue. Check your spam folder if you didn't receive it."}

@app.post("/api/user/delete")
async def apiDeleteAccount(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    token = form['token']
    
    cur.execute(f"DELETE FROM EmailVerification WHERE operation = 'delete_account' AND expire <= {int(time.time()) - 600}")
    conn.commit()

    token = form["token"]
    token = token
    
    if token == "" or not token.replace("-","").replace("_","").isalnum():
        return {"success": False, "msg": "Invalid or expired verification token!"}

    cur.execute(f"SELECT userId FROM EmailVerification WHERE operation = 'delete_account' AND token = '{token}'")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Invalid or expired verification token!"}

    userId = t[0][0]
    
    email = ""
    username = ""
    cur.execute(f"SELECT email, username FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        email = t[0][0]
        username = decode(t[0][1])

    sessions.markDeletion(userId)

    ip = request.headers["CF-Connecting-Ip"]
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'delete_account', {int(time.time())}, '{encode(f'Account marked for deletion by {ip}')}')")
    sessions.logout(userId, token)
    conn.commit()

    if validators.email(email) == True:
        background_tasks.add_task(sendNormal, email, username, "Account marked for deletion", f"Your account has been marked for deletion. It will be deleted after 14 days.<br>\n\
            If you have changed your mind, login again to recover your account.")

    return {"success": True, "msg": "Your account has been marked for deletion!"}

@app.post("/api/user/validate")
async def apiValidateToken(request: Request):
    form = await request.form()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        return {"success": True, "validation": False}
    userId = int(form["userId"])
    token = form["token"]
    return {"success": True, "validation": validateToken(userId, token)}

@app.post("/api/user/info")
async def apiGetUserInfo(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    d = None
    cur.execute(f"SELECT username, email, inviteCode, inviter, bio FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        d = t[0]
    else:
        return {"success": False, "msg": "User not found!"}
    d = list(d)
    d[0] = decode(d[0])
    d[4] = decode(d[4])
    email = d[1]

    cur.execute(f"DELETE FROM PendingEmailChange WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT email FROM PendingEmailChange WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0 and not t[0][0].startswith("!"):
        email = email + " -> " + t[0][0] + " (Not verified)"

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
    else:
        username = f"<a href='/user?userId={userId}'><span>{username}</span></a>"

    goal = 99999
    cur.execute(f"SELECT goal FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        goal = t[0][0]
    
    chtoday = 0
    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {userId} AND memorized = 1 AND timestamp >= {int(time.time()/86400)*86400}")
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

    return {"success": True, "username": username, "bio": d[4], "email": email, "invitationCode": d[2], "inviter": inviter, "age": age, "isAdmin": isAdmin, \
        "goal": goal, "chtoday": chtoday, "checkin_today": checkin_today, "checkin_continuous": checkin_continuous}

@app.post("/api/user/goal")
async def apiGetUserGoal(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    goal = 99999
    cur.execute(f"SELECT goal FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        goal = t[0][0]
    
    chtoday = 0
    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {userId} AND memorized = 1 AND timestamp >= {int(time.time()/86400)*86400}")
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
    
    return {"success": True, "goal": goal, "chtoday": chtoday, "checkin_today": checkin_today, "checkin_continuous": checkin_continuous}

@app.post("/api/user/updateGoal")
async def apiUserUpdateGoal(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    goal = int(form["goal"])

    if goal <= 0:
        return {"success": True, "msg": "Goal must be a positive number!"}

    cur.execute(f"UPDATE UserInfo SET goal = {goal} WHERE userId = {userId}")
    conn.commit()

    return {"success": True, "msg": "Goal updated!"}

@app.post("/api/user/checkin")
async def apiUserCheckin(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    cur.execute(f"SELECT * FROM CheckIn WHERE userId = {userId} AND timestamp >= {int(time.time()/86400)*86400}")
    if len(cur.fetchall()) > 0:
        return {"success": False, "msg": "You have already checked in today!"}
    
    goal = 0
    cur.execute(f"SELECT goal FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        goal = t[0][0]

    if goal == 0:
        return {"success": False, "msg": "Have a goal first!"}
    
    chtoday = 0
    cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {userId} AND memorized = 1 AND timestamp >= {int(time.time()/86400+86400) - 86400}")
    t = cur.fetchall()
    if len(t) > 0:
        chtoday = t[0][0]

    if chtoday < goal:
        return {"success": False, "msg": "You haven't accomplished today's goal!"}
        
    cur.execute(f"INSERT INTO CheckIn VALUES ({userId}, {int(time.time())})")
    conn.commit()

    return {"success": True, "msg": "Checked in successfully!"}

@app.get("/api/user/chart/{uid}")
async def apiGetUserChart(uid: int, request: Request):
    conn = newconn()
    cur = conn.cursor()
    
    cur.execute(f"SELECT * FROM UserInfo WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "User not found!"}
    
    d1 = []
    batch = 3
    for i in range(30):
        cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {uid} AND memorized = 1 AND timestamp >= {int(time.time()/86400+1)*86400 - 86400*batch*(i+1)} AND timestamp <= {int(time.time()/86400+1)*86400 - 86400*batch*i}")
        t = cur.fetchall()
        memorized = 0
        if len(t) > 0:
            memorized = t[0][0]

        cur.execute(f"SELECT COUNT(*) FROM ChallengeRecord WHERE userId = {uid} AND memorized = 0 AND timestamp >= {int(time.time()/86400+1)*86400 - 86400*batch*(i+1)} AND timestamp <= {int(time.time()/86400+1)*86400 - 86400*batch*i}")
        t = cur.fetchall()
        forgotten = 0
        if len(t) > 0:
            forgotten = t[0][0]
        
        d1.append({"index": 30 - i, "memorized": memorized, "forgotten": forgotten})
    
    d2 = []
    total_memorized = 0
    batch = 3
    for i in range(30):
        cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {uid} AND memorizedTimestamp != 0 AND memorizedTimestamp <= {int(time.time()/86400+1)*86400 - 86400*batch*i}")
        t = cur.fetchall()
        total = 0
        if len(t) > 0:
            total = t[0][0]
        total_memorized = max(total_memorized, total)
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

    return {"success": True, "challenge_history": d1, "total_memorized_history": d2, "tag_cnt": tagcnt, "del_cnt": delcnt, "total_memorized": total_memorized, "total": cnt}

@app.get("/api/user/publicInfo/{uid:int}")
async def apiGetUserPublicInfo(uid: int, request: Request):
    conn = newconn()
    cur = conn.cursor()
    
    cur.execute(f"SELECT username, bio FROM UserInfo WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) == 0 or uid < 0:
        return {"success": False, "msg": "User not found!"}
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
    else:
        username = f"<a href='/user?userId={uid}'><span>{username}</span></a>"

    return {"success": True, "username": username, "bio": bio, "cnt": cnt, "tagcnt": tagcnt, "delcnt": delcnt, "chcnt": chcnt, "age": age, "isAdmin": isAdmin}   

@app.post("/api/user/events")
async def apiUserEvents(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    page = int(form["page"])
    
    cur.execute(f"SELECT timestamp, msg FROM UserEvent WHERE userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()
    ret = []
    for dd in d:
        ret.append({"timestamp": dd[0], "msg": decode(dd[1])})
    
    if len(ret) <= (page - 1) * 20:
        return {"notifications": [], "nextpage": -1}
    elif len(ret) <= page * 20:
        return {"notifications": ret[(page - 1) * 20 + 1 :], "nextpage": -1}
    else:
        return {"notifications": ret[(page - 1) * 20 + 1 : page * 20 + 1], "nextpage": page + 1}

@app.post("/api/user/sessions")
async def apiUserSessions(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    ss = []
    cur.execute(f"SELECT loginTime, expireTime, ua, ip, token FROM ActiveUserLogin WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        if dd[1] <= int(time.time()):
            cur.execute(f"DELETE FROM ActiveUserLogin WHERE token = '{dd[4]}' AND userId = {userId}")
        else:
            ss.append({"loginTime": dd[0], "expireTime": dd[1], "userAgent": decode(dd[2]), "ip": decode(dd[3])})
    
    return ss

@app.post("/api/user/updateInfo")
async def apiUpdateInfo(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)

    if OPLimit(userId, "update_info"):
        return {"success": False, "msg": "Too many requests! Try again later!"}    
    
    username = form["username"]
    email = form["email"]
    bio = form["bio"]

    if username is None or email is None\
        or username.replace(" ","") == "" or email.replace(" ","") == "":
        return {"success": False, "msg": "Username and email must be filled!"}
    if " " in username or "(" in username or ")" in username or "[" in username or "]" in username or "{" in username or "}" in username \
        or "<" in username or ">" in username \
            or "!" in username or "@" in username or "'" in username or '"' in username or "/" in username or "\\" in username :
        return {"success": False, "msg": "Username must not contain: spaces, ( ) [ ] { } < > ! @ ' \" / \\"}
    username = encode(username)
    if validators.email(email) != True or "'" in email or '"' in email:
        return {"success": False, "msg": "Invalid email!"}
    bio = encode(bio)
    
    cur.execute(f"SELECT username, email, userId FROM UserInfo")
    t = cur.fetchall()
    for tt in t:
        if tt[2] == userId:
            continue
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if decode(tt[1]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}
    
    if len(username) >= 256:
        return {"success": False, "msg": "Username too long!"}
    if len(bio) >= 4096:
        return {"success": False, "msg": "Bio too long!"}
    if len(email) >= 128:
        return {"success": False, "msg": "Email too long!"}
    
    cur.execute(f"UPDATE UserInfo SET username = '{username}' WHERE userId = {userId}")
    cur.execute(f"UPDATE UserInfo SET bio = '{bio}' WHERE userId = {userId}")
    conn.commit()

    cur.execute(f"SELECT email FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0 and t[0][0].lower() != email.lower():
        token = b62encode(int(time.time())) + "-" + str(uuid.uuid4())
        background_tasks.add_task(sendVerification, email, decode(username), "Email update verification", \
            f"You are changing your email address to {email}. Please open the link to verify this new address.", "10 minutes", \
                "https://memo.charles14.xyz/user/verify?type=changeemail&token="+token)
        cur.execute(f"SELECT email FROM PendingEmailChange WHERE userId = {userId}")
        p = cur.fetchall()
        for pp in p:
            e = pp[0]
            if not e.startswith("!"):
                cur.execute(f"DELETE FROM PendingEmailChange WHERE userId = {userId} AND email = '{e}'")
        cur.execute(f"INSERT INTO PendingEmailChange VALUES ({userId}, '{email}', '{token}', {int(time.time()+600)})")
        conn.commit()
        return {"success": True, "msg": "User profile updated, but email is not updated! \
            Please check the inbox of the new email and open the link in it to verify it!"}
    else:
        cur.execute(f"UPDATE UserInfo SET email = '{email}' WHERE userId = {userId}") # maybe capital case changes
        conn.commit()
        return {"success": True, "msg": "User profile updated!"}

@app.post("/api/user/changeemail/verify")
async def apiChangeEmailVerify(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()

    token = form["token"]
    token = token
    
    if token == "" or not token.replace("-","").replace("_","").isalnum():
        return {"success": False, "msg": "Invalid or expired verification token!"}

    cur.execute(f"SELECT userId, email, expire FROM PendingEmailChange WHERE token = '{token}'")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Invalid or expired verification token!"}
    
    if t[0][2] <= int(time.time()):
        cur.execute(f"DELETE FROM PendingEmailChange WHERE token = '{token}'")
        conn.commit()
        return {"success": False, "msg": "Verification token expired! Please register again!"}
    
    userId = t[0][0]
    newEmail = t[0][1]
    revert = False
    if newEmail.startswith("!"):
        revert = True
        newEmail = newEmail[1:]

    cur.execute(f"SELECT username, email FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        username = decode(t[0][0])
        oldEmail = t[0][1]
        if not revert:
            newtoken = b62encode(int(time.time())) + "-" + str(uuid.uuid4())
            background_tasks.add_task(sendNormal, oldEmail, username, "Email updated", f"Your email has been updated to {newEmail}.<br>\n\
                If you didn't do this, open the link below to change it back, the link is valid for 7 days.<br>\n\
                    <a href='https://memo.charles14.xyz/user/verify?token="+newtoken+"'>https://memo.charles14.xyz/user/verify?token="+newtoken+"</a>")
            cur.execute(f"INSERT INTO PendingEmailChange VALUES ({userId}, '!{oldEmail}', '{newtoken}', {int(time.time()+86400*7)})")
            conn.commit()

    cur.execute(f"INSERT INTO EmailHistory VALUES ({userId}, '{newEmail.lower()}', {int(time.time())})")
    cur.execute(f"UPDATE UserInfo SET email = '{newEmail}' WHERE userId = {userId}")
    cur.execute(f"DELETE FROM PendingEmailChange WHERE token = '{token}'")
    conn.commit()

    return {"success": True, "msg": f"Email updated to {newEmail}"}

@app.post("/api/user/changepassword")
async def apiChangePassword(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    oldpwd = form["oldpwd"]
    newpwd = form["newpwd"]
    cfmpwd = form["cfmpwd"]
    
    pwd = ""
    cur.execute(f"SELECT password FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        pwd = t[0][0]
    if not checkpwd(oldpwd, decode(pwd)):
        return {"success": False, "msg": "Incorrect old password!"}

    if newpwd != cfmpwd:
        return {"success": False, "msg": "New password and confirm password mismatch!"}

    newhashed = hashpwd(newpwd)
    cur.execute(f"UPDATE UserInfo SET password = '{encode(newhashed)}' WHERE userId = {userId}")
    
    ip = request.headers["CF-Connecting-Ip"]
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'change_password', {int(time.time())}, '{encode(f'Password changed by {ip}')}')")
    sessions.logoutAll(userId)
    conn.commit()

    return {"success": True}

@app.post("/api/user/settings")
async def apiUserSettings(request: Request):
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    op = form["operation"]

    if op == "upload":    
        rnd = int(form["random"])
        swp = int(form["swap"])
        showStatus = int(form["showStatus"])
        mode = int(form["mode"])
        ap = int(form["autoPlay"])
        theme = form["theme"]
        if not theme in ["light","dark"]:
            return {"success": False, "msg": "Theme can only be light or dark"}

        cur.execute(f"DELETE FROM UserSettings WHERE userId = {userId}")
        cur.execute(f"INSERT INTO UserSettings VALUES ({userId}, {rnd}, {swp}, {showStatus}, {mode}, {ap}, '{theme}')")
        conn.commit()

        return {"success": True, "msg": "Settings synced!"}
    
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
                
        return {"success": True, "msg": "Settings synced!", "random": rnd, "swap": swp, "showStatus": showStatus,\
            "mode": mode, "autoPlay": autoPlay, "theme": theme}