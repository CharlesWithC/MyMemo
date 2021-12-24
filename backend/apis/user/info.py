# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import os, sys, time, math
import json

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# User Info API

@app.post("/api/user/info")
async def apiGetUserInfo(request: Request):
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
    email = decode(d[1])

    cur.execute(f"DELETE FROM PendingEmailChange WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT email FROM PendingEmailChange WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0 and not t[0][0].startswith("!"):
        email = email + " -> " + decode(t[0][0]) + " (Not verified)"

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
        username = f"<a href='/user?userId={userId}'><span class='username' style='color:{t[0][1]}'>{username}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
    else:
        username = f"<a href='/user?userId={userId}'><span class='username'>{username}</span></a>"

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

@app.get("/api/user/publicInfo/{uid:int}")
async def apiGetUserPublicInfo(uid: int, request: Request):
    ip = request.client.host
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
        username = f"<a href='/user?userId={uid}'><span class='username' style='color:{t[0][1]}'>{username}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
    else:
        username = f"<a href='/user?userId={uid}'><span class='username'>{username}</span></a>"

    return {"success": True, "username": username, "bio": bio, "cnt": cnt, "tagcnt": tagcnt, "delcnt": delcnt, "chcnt": chcnt, "age": age, "isAdmin": isAdmin}   

@app.get("/api/user/chart/{uid}")
async def apiGetUserChart(uid: int, request: Request):
    ip = request.client.host
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

@app.post("/api/user/goal")
async def apiGetUserGoal(request: Request):
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

@app.post("/api/user/events")
async def apiUserEvents(request: Request):
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
    
    page = int(form["page"])
    
    cur.execute(f"SELECT timestamp, msg FROM UserEvent WHERE userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()
    ret = []
    for dd in d:
        ret.append({"timestamp": dd[0], "msg": decode(dd[1])})
    
    if len(ret) <= (page - 1) * 20:
        return {"success": True, "notifications": [], "nextpage": -1}
    elif len(ret) <= page * 20:
        return {"success": True, "notifications": ret[(page - 1) * 20 :], "nextpage": -1}
    else:
        return {"success": True, "notifications": ret[(page - 1) * 20 : page * 20], "nextpage": page + 1}

@app.post("/api/user/sessions")
async def apiUserSessions(request: Request):
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
    
    ss = []
    cur.execute(f"SELECT loginTime, expireTime, ua, ip, token FROM ActiveUserLogin WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        if dd[1] <= int(time.time()):
            cur.execute(f"DELETE FROM ActiveUserLogin WHERE token = '{dd[4]}' AND userId = {userId}")
        else:
            ss.append({"loginTime": dd[0], "expireTime": dd[1], "userAgent": decode(dd[2]), "ip": dd[3]})
    
    return ss
