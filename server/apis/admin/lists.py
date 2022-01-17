# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks
from ansi2html import Ansi2HTMLConverter
import os, time, datetime

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Admin User List API

@app.post("/api/admin/userList")
async def apiAdminUserList(request: Request):
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

    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        raise HTTPException(status_code=401)

    page = int(form["page"])
    if page <= 0:
        page = 1

    pageLimit = int(form["pageLimit"])
    if pageLimit <= 0:
        pageLimit = 20
    
    if pageLimit > 100:
        return {"success": True, "data": [], "total": 0}

    orderBy = form["orderBy"] # userId, username, email, inviter, inviteCode, age, status, privilege
    if not orderBy in ["none", "userId", "username", "email", "inviter", "inviteCode", "age", "status", "privilege"]:
        orderBy = "userId"
    if orderBy == "username":
        orderBy = "plain_username"
    if orderBy == "age":
        orderBy = "int_age"

    order = form["order"]
    if not order in ["asc", "desc"]:
        order = "asc"
    l = {"asc": 0, "desc": 1}
    order = l[order]

    search = form["search"]
    if search == "" and orderBy == "none":
        orderBy = "plain_username"

    cur.execute(f"SELECT userId FROM AdminList")
    admins = cur.fetchall()
        
    cur.execute(f"SELECT userId, value FROM Privilege WHERE item = 'mute'")
    muted = cur.fetchall()
    
    cur.execute(f"SELECT userId, username, email, inviter, inviteCode FROM UserInfo")
    d = cur.fetchall()
    users = []
    for dd in d:
        dd = list(dd)
        dd[1] = decode(dd[1])

        userType = 0
        status = "Active"
        if dd[0] < 0:
            userType = 2
            status = "Banned"
        if dd[1] == "@deleted":
            userType = 3
            status = "Deleted"
        if sessions.checkDeletionMark(dd[0]):
            userType = 4
            status = "Deactivated"

        muteUntil = 0
        for mm in muted:
            if abs(mm[0]) == abs(dd[0]):
                userType = 2
                muteUntil = mm[1]
                status += ", Muted"

        isAdmin = False
        if (dd[0],) in admins:
            isAdmin = True
            userType = 1
            status += " , Admin"
        
        inviterUsername = "Unknown"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) != 0:
            inviterUsername = decode(t[0][0])

        regts = 0
        cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {abs(dd[0])} AND event = 'register'")
        t = cur.fetchall()
        if len(t) > 0:
            regts = t[0][0]

        prv = ""
        cur.execute(f"SELECT item, value FROM Privilege WHERE userId = {abs(dd[0])}")
        t = cur.fetchall()
        if len(t) == 0:
            prv = "/"
        else:
            for tt in t:
                if tt[0] == "mute":
                    continue
                prv += str(tt[0]) + ": " + str(tt[1])
                prv += ", "
            prv = prv[:-2]
            if prv == "":
                prv = "/"

        username = dd[1]
        plain_username = dd[1]
        if username != "@deleted" and dd[0] != 0:
            cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {abs(dd[0])}")
            t = cur.fetchall()
            if len(t) > 0:
                username = f"<a href='/user?userId={dd[0]}'><span class='username' style='color:{t[0][1]}'>{username}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
            else:
                username = f"<a href='/user?userId={dd[0]}'><span class='username'>{username}</span></a>"

        if dd[3] != 0:
            cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {abs(dd[3])}")
            t = cur.fetchall()
            if len(t) > 0:
                inviterUsername = f"<a href='/user?userId={dd[3]}'><span class='username' style='color:{t[0][1]}'>{inviterUsername}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
            else:
                inviterUsername = f"<a href='/user?userId={dd[3]}'><span class='username'>{inviterUsername}</span></a>"
        
        inviterInfo = f"{inviterUsername} (UID: {dd[3]})"
        if inviterUsername == "default":
            inviterInfo = "/"

        email = "/"
        if dd[0] != 0 and username != "@deleted":
            email = decode(dd[2])
        
        inviteCode = dd[4]
        if inviteCode == "":
            inviteCode = "/"

        banReason = ""        
        if dd[0] < 0:
            cur.execute(f"SELECT reason FROM BanReason WHERE userId = {-dd[0]}")
            t = cur.fetchall()
            if len(t) > 0:
                banReason = decode(t[0][0])

        users.append({"userId": str(dd[0]), "username": username, "plain_username": plain_username, "email": email, \
            "inviter": inviterInfo, "inviteCode": inviteCode, "int_age": int(time.time() - regts), "age": CalculateAge(regts), \
                "userType": userType, "isAdmin": isAdmin, "status": status, "privilege": prv, \
                    "banReason": banReason, "muteUntil": muteUntil})
        
    cur.execute(f"SELECT puserId, username, email, inviter FROM UserPending")
    d = cur.fetchall()
    users_pending = []
    for dd in d:
        dd = list(dd)
        
        inviterUsername = "Unknown"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) != 0:
            inviterUsername = decode(t[0][0])

        users_pending.append({"userId": str(dd[0]) + "*", "username": decode(dd[1]), "plain_username": decode(dd[1]), \
            "email": decode(dd[2]), "inviter": f"{inviterUsername} (UID: {dd[3]})", "inviteCode": "/", \
                "int_age": 0, "age": "0 day", "userType": 5, "isAdmin": False, "status": "Pending Activation", "privilege": "/", \
                    "banReason": "", "muteUntil": ""})

    t = {}
    for dd in users:
        ok = False
        for tt in dd.keys():
            if search == "" or search in str(dd[tt]):
                ok = True
                break
        if not ok:
            continue
        if orderBy == "userId" or orderBy == "none":
            t[abs(int(dd["userId"]))] = dd
        elif orderBy == "int_age":
            t[str(dd["int_age"]).zfill(20) + str(dd["userId"].replace("*","")).zfill(20)] = dd
        else:
            t[str(dd[orderBy]) + "<id>" + str(dd["userId"])] = dd
    ret1 = []
    if orderBy != "none":
        for key in sorted(t.keys()):
            ret1.append(t[key])
    else:
        for key in t.keys():
            ret1.append(t[key])
    if order == 1:
        ret1 = ret1[::-1]

    t = {}
    for dd in users_pending:
        ok = False
        for tt in dd.keys():
            if search == "" or search in str(dd[tt]):
                ok = True
                break
        if not ok:
            continue
        if orderBy == "userId" or orderBy == "int_age" or orderBy == "none":
            t[int(dd["userId"].replace("*",""))] = dd
        else:
            t[str(dd[orderBy]) + "<id>" + str(dd["userId"].replace("*",""))] = dd
    ret2 = []
    for key in sorted(t.keys()):
        ret2.append(t[key])
    if order == 1:
        ret2 = ret2[::-1]

    ret = ret1 + ret2
    
    if len(ret) <= (page - 1) * pageLimit:
        return {"success": True, "data": [], "total": (len(ret) - 1) // pageLimit + 1, "totalUser": len(ret)}
    elif len(ret) <= page * pageLimit:
        return {"success": True, "data": ret[(page - 1) * pageLimit :], "total": (len(ret) - 1) // pageLimit + 1, "totalUser": len(ret)}
    else:
        return {"success": True, "data": ret[(page - 1) * pageLimit : page * pageLimit], "total": (len(ret) - 1) // pageLimit + 1, "totalUser": len(ret)}

@app.post("/api/admin/log")
async def apiAdminLog(request: Request):
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

    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        raise HTTPException(status_code=401)
    
    if userId != 1:
        return {"success": False, "clientIp": ip, "log": "<pre>Only site owner can view server log!</pre>"}

    start = int(form["start"])
    end = int(form["end"])
    reverse = int(form["reverse"])

    d = open(config.log_file, "r").read().split("\n")[:-1]
    if len(d) < start or end <= 0:
        return {"success": False}
    start = max(0, start)
    start_line = 0
    ret = ""
    if reverse:
        head = max(len(d) - end, 0)
        tail = len(d) - start
        ret = "\n".join(d[::-1][head:tail][::-1])
    else:
        head = start
        tail = min(len(d), end)
        ret = "\n".join(d[head:tail])
    
    if head == tail:
        return {"success": False, "clientIp": ip, "serverTime": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

    conv = Ansi2HTMLConverter()
    html = conv.convert(ret)

    return {"success": True, "head": head, "tail": tail, "log": html, "clientIp": ip, "serverTime": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}