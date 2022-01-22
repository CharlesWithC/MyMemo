# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks
import time, uuid
import validators

from app import app, config
from db import newconn
from functions import *
import sessions
from emailop import sendVerification

##########
# User Register API

@app.post("/api/user/register")
async def apiRegister(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    if not config.allow_register:
        return {"success": False, "msg": "Public register not enabled!"}
        
    conn = newconn()
    cur = conn.cursor()

    captchaToken = form["captchaToken"]
    captchaAnswer = form["captchaAnswer"]
    captchaResult = validateCaptcha(captchaToken, captchaAnswer)
    if captchaResult != True:
        return captchaResult

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
    if not username.isalnum():
        return {"success": False, "msg": "Username must not contain special characters!"}
    username = encode(username)
    if validators.email(email) != True:
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
        if decode(tt[1]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    cur.execute(f"DELETE FROM PendingEmailChange WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT email FROM PendingEmailChange")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}
        elif tt[0].startswith("!") and decode(tt[0].lower()[1:]) == email.lower():
            return {"success": False, "msg": "The previous owner of this email has updated their email within 7 days so this email address is reserved for 7 days!"}

    cur.execute(f"SELECT username, email FROM UserInfo")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if decode(tt[1]).lower() == email.lower():
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

    if OPLimit(ip, "register", maxop = 1):
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

        cur.execute(f"INSERT INTO UserPending VALUES ({puserId}, '{username}', '{encode(email)}', '{encode(password)}', {inviter}, '{token}', {int(time.time() + 3600 * 3)})")
        conn.commit()
    except:
        sessions.errcnt += 1
        return {"success": False, "msg": "Unknown error occured. Try again later..."}

    return {"success": True, "msg": "Account registered, but pending activation! \
        Check your email and open the verification link to activate your account! \
        The link expires in 3 hours. After that your account will be removed and you need to register again!"}

@app.post("/api/user/activate")
async def apiActivate(request: Request):
    ip = request.client.host
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
    email = decode(t[0][1])
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

        cur.execute(f"INSERT INTO UserInfo VALUES ({userId}, '{username}', '', '{encode(email)}', '{password}', {inviter}, '{inviteCode}', 99999)")
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
    cur.execute(f"INSERT INTO EmailHistory VALUES ({userId}, '{encode(email)}', {int(time.time())})")
    conn.commit()

    return {"success": True, "msg": "Account activated!"}

@app.post("/api/user/pending/getInfo")
async def apiUserPendingGetInfo(request: Request):
    ip = request.client.host
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
    email = decode(t[0][1])

    return {"success": True, "username": username, "email": email}

@app.post("/api/user/pending/updateInfo")
async def apiUserPendingUpdateInfo(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
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
    if not username.isalnum():
        return {"success": False, "msg": "Username must not contain special characters!"}
    username = encode(username)
    if validators.email(email) != True:
        return {"success": False, "msg": "Invalid email!"}

    cur.execute(f"SELECT username, email FROM UserPending WHERE puserId != {puserId}")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if decode(tt[1]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    cur.execute(f"DELETE FROM PendingEmailChange WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT email FROM PendingEmailChange")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}
        elif tt[0].startswith("!") and decode(tt[0].lower()[1:]) == email.lower():
            return {"success": False, "msg": "The previous owner of this email has updated their email within 7 days so this email address is reserved for 7 days!"}

    cur.execute(f"SELECT username, email FROM UserInfo")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if decode(tt[1]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    cur.execute(f"UPDATE UserPending SET username = '{username}' WHERE puserId = {puserId}")
    cur.execute(f"UPDATE UserPending SET email = '{encode(email)}' WHERE puserId = {puserId}")
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