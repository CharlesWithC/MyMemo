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
# User Manage API

@app.post("/api/user/updateInfo")
async def apiUpdateInfo(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)

    if OPLimit(userId, "update_info", 10):
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
    if validators.email(email) != True:
        return {"success": False, "msg": "Invalid email!"}
    bio = encode(bio)
    
    cur.execute(f"SELECT username, email, userId FROM UserInfo WHERE userId != {userId}")
    t = cur.fetchall()
    for tt in t:
        if tt[2] == userId:
            if decode(tt[0]).lower() != decode(username).lower():
                cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'update_username', {int(time.time())}, '{encode(f'Updated username to {username}')}')")
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
    if len(t) > 0 and decode(t[0][0]).lower() != email.lower():
        if not "captchaToken" in form.keys() or not "captchaAnswer" in form.keys():
            return {"success": False, "captcha": True}
        captchaToken = form["captchaToken"]
        captchaAnswer = form["captchaAnswer"]
        captchaResult = validateCaptcha(captchaToken, captchaAnswer)
        if captchaResult != True:
            return captchaResult

        token = b62encode(int(time.time())) + "-" + str(uuid.uuid4())
        background_tasks.add_task(sendVerification, email, decode(username), "Email update verification", \
            f"You are changing your email address to {email}. Please open the link to verify this new address.", "10 minutes", \
                "https://memo.charles14.xyz/user/verify?token="+token)
        cur.execute(f"DELETE FROM PendingEmailChange WHERE userId = {userId}")
        cur.execute(f"INSERT INTO PendingEmailChange VALUES ({userId}, '{encode(email)}', '{token}', {int(time.time()+600)})")
        conn.commit()
        return {"success": True, "msg": "User profile updated, but email is not updated! \
            Please check the inbox of the new email and open the link in it to verify it!"}
    else:
        cur.execute(f"UPDATE UserInfo SET email = '{encode(email)}' WHERE userId = {userId}") # maybe capital case changes
        conn.commit()
        return {"success": True, "msg": "User profile updated!"}

@app.post("/api/user/updateGoal")
async def apiUserUpdateGoal(request: Request):
    ip = request.client.host
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
    ip = request.client.host
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

@app.post("/api/user/changeemail/verify")
async def apiChangeEmailVerify(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
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
    newEmail = decode(t[0][1])
    revert = False
    if newEmail.startswith("!"):
        revert = True
        newEmail = newEmail[1:]

    cur.execute(f"SELECT username, email FROM UserInfo WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        username = decode(t[0][0])
        oldEmail = decode(t[0][1])
        if not revert:
            newtoken = b62encode(int(time.time())) + "-" + str(uuid.uuid4())
            background_tasks.add_task(sendNormal, oldEmail, username, "Email updated", f"Your email has been updated to {newEmail}.<br>\n\
                If you didn't do this, open the link below to change it back, the link is valid for 7 days.<br>\n\
                    <a href='https://memo.charles14.xyz/user/verify?token="+newtoken+"'>https://memo.charles14.xyz/user/verify?token="+newtoken+"</a>")
            cur.execute(f"INSERT INTO PendingEmailChange VALUES ({userId}, '!{oldEmail}', '{newtoken}', {int(time.time()+86400*7)})")
            conn.commit()

    cur.execute(f"INSERT INTO EmailHistory VALUES ({userId}, '{newEmail.lower()}', {int(time.time())})")
    cur.execute(f"UPDATE UserInfo SET email = '{encode(newEmail)}' WHERE userId = {userId}")
    cur.execute(f"DELETE FROM PendingEmailChange WHERE token = '{token}'")
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'update_email', {int(time.time())}, '{encode(f'Updated email to {newEmail}')}')")
    conn.commit()

    return {"success": True, "msg": f"Email updated to {newEmail}"}

@app.post("/api/user/changepassword")
async def apiChangePassword(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)

    if OPLimit(userId, "change_password", 3):
        return {"success": False, "msg": "Too many requests! Try again later!"}    
    
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
    
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'change_password', {int(time.time())}, '{encode(f'Password changed by {ip}')}')")
    sessions.logoutAll(userId)
    conn.commit()

    return {"success": True}

@app.post("/api/user/settings")
async def apiUserSettings(request: Request):
    ip = request.client.host
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

@app.post("/api/user/requestDelete")
async def apiRequestDeleteAccount(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
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
    
    if OPLimit(userId, "account_deletion", 1):
        return {"success": False, "msg": "Too many requests! Try again later!"}    

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
        email = decode(d[0][1])
        
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
    ip = request.client.host
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
        email = decode(t[0][0])
        username = decode(t[0][1])

    sessions.markDeletion(userId)

    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'delete_account', {int(time.time())}, '{encode(f'Account marked for deletion by {ip}')}')")
    sessions.logout(userId, token)
    conn.commit()

    if validators.email(email) == True:
        background_tasks.add_task(sendNormal, email, username, "Account marked for deletion", f"Your account has been marked for deletion. It will be deleted after 14 days.<br>\n\
            If you have changed your mind, login again to recover your account.")

    return {"success": True, "msg": "Your account has been marked for deletion!"}