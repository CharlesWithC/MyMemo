# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException

from app import app, config
from db import newconn
from functions import *

##########
# Group API
# Info, Preview

@app.post("/api/group/info")
async def apiGroupMember(request: Request):
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

    groupId = int(form["groupId"])
    cur.execute(f"SELECT userId, isEditor FROM GroupMember WHERE groupId = {groupId}")
    d = cur.fetchall()
    if not (userId,0,) in d and not (userId,1,) in d:
        return {"success": False, "msg": f"You must be a member of the group before viewing its info."}

    info = None
    cur.execute(f"SELECT name, description, anonymous FROM GroupInfo WHERE groupId = {groupId}")
    t = cur.fetchall()
    if len(t) > 0:
        info = t[0]
    else:
        return {"success": False, "msg": "Group not found!"}

    return {"success": True, "name": decode(info[0]), "description": decode(info[1])}

@app.post("/api/group/member")
async def apiGroupMember(request: Request):
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
    
    groupId = int(form["groupId"])
    cur.execute(f"SELECT userId, isEditor FROM GroupMember WHERE groupId = {groupId}")
    d = cur.fetchall()
    if not (userId,0,) in d and not (userId,1,) in d:
        return {"success": False, "msg": f"You must be a member of the group before viewing its members."}
    
    cur.execute(f"SELECT * FROM GroupQuestion WHERE groupId = {groupId}")
    questioncnt = len(cur.fetchall())
    cur.execute(f"SELECT groupQuestionId FROM GroupQuestion WHERE groupId = {groupId}")
    questions = cur.fetchall()

    info = None
    cur.execute(f"SELECT name, description, anonymous FROM GroupInfo WHERE groupId = {groupId}")
    t = cur.fetchall()
    if len(t) > 0:
        info = t[0]
    else:
        return {"success": False, "msg": "Group not found!"}

    owner = 0
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    t = cur.fetchall()
    if len(t) > 0:
        owner = t[0][0]
        if owner < 0:
            return {"success": False, "msg": "Group is invisible because its owner is banned."}
    
    isOwner = False
    if owner == userId:
        isOwner = True

    ret = []
    for dd in d:
        uid = dd[0]
        isEditor = dd[1]

        if uid < 0:
            continue
        
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
        t = cur.fetchall()
        if len(t) == 0:
            continue
        
        username = decode(t[0][0])
        plain_username = username

        if owner == uid:
            username = username + " (Owner)"
        elif isEditor:
            username = username + " (Editor)"
        
        bookId = -1
        cur.execute(f"SELECT bookId FROM GroupMember WHERE groupId = {groupId} AND userId = {uid}")
        t = cur.fetchall()
        if len(t) > 0:
            bookId = t[0][0]
        cur.execute(f"SELECT progress FROM Book WHERE userId = {uid} AND bookId = {bookId}")
        p = cur.fetchall()
        pgs = 0
        if len(p) != 0:
            pgs = p[0][0]
        
        pgs = f"{pgs} / {questioncnt}"

        if info[2] == 0:
            cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {uid}")
            t = cur.fetchall()
            if len(t) > 0:
                username = f"<a href='/user/{uid}'><span class='username' style='color:{t[0][1]}'>{username}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
            else:
                username = f"<a href='/user/{uid}'><span class='username'>{username}</span></a>"
            ret.append({"userId": uid, "username": username, "plain_username": plain_username, "progress": pgs})
        elif info[2] == 1:
            ret.append({"userId": 0, "username": "Anonymous", "plain_username": "Anonymous", "progress": pgs})
        elif info[2] == 2:
            ret.append({"userId": 0, "username": "Anonymous", "plain_username": "Anonymous", "progress": "Unknown"})

    page = int(form["page"])
    if page <= 0:
        page = 1

    pageLimit = int(form["pageLimit"])
    if pageLimit <= 0:
        pageLimit = 20
    
    if pageLimit > 100:
        return {"success": True, "data": [], "total": 0}

    orderBy = form["orderBy"]
    if not orderBy in ["none", "username", "progress"]:
        orderBy = "progress"
    if orderBy == "username":
        orderBy = "plain_username"

    order = form["order"]
    if not order in ["asc", "desc"]:
        order = "asc"
    l = {"asc": 0, "desc": 1}
    order = l[order]

    search = form["search"]
    if search == "" and orderBy == "none":
        orderBy = "plain_username"

    t = {}
    i = 0
    for dd in ret:
        if search != "" and not search in str(dd["plain_username"]):
            continue
        i += 1
        t[str(dd[orderBy]) + "<id>" + str(dd["userId"]) + str(i)] = dd
        
    ret = []
    if orderBy != "none":
        for key in sorted(t.keys()):
            ret.append(t[key])
    else:
        for key in t.keys():
            ret.append(t[key])
    if order == 1:
        ret = ret[::-1]

    if len(ret) <= (page - 1) * pageLimit:
        return {"success": True, "data": [], "total": (len(ret) - 1) // pageLimit + 1, "totalMember": len(ret),\
             "name": decode(info[0]), "description": decode(info[1]), "isOwner": isOwner}
    elif len(ret) <= page * pageLimit:
        return {"success": True, "data": ret[(page - 1) * pageLimit :], "total": (len(ret) - 1) // pageLimit + 1, "totalMember": len(ret),\
             "name": decode(info[0]), "description": decode(info[1]), "isOwner": isOwner}
    else:
        return {"success": True, "data": ret[(page - 1) * pageLimit : page * pageLimit], "total": (len(ret) - 1) // pageLimit + 1, "totalMember": len(ret),\
             "name": decode(info[0]), "description": decode(info[1]), "isOwner": isOwner}

@app.post("/api/group/preview")
async def apiGroupPreview(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    
    groupCode = form["groupCode"]

    if groupCode.startswith("@"):
        groupCode = groupCode[1:]
    
    if not groupCode.isalnum():
        return {"success": False, "msg": "Invalid group code!"}

    cur.execute(f"SELECT groupId, owner, name, description FROM GroupInfo WHERE groupCode = '{groupCode}'")
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Invalid group code!"}
    d = d[0]
    groupId = d[0]
    owner = d[1]
    name = decode(d[2])
    description = decode(d[3])

    memberCount = 0
    cur.execute(f"SELECT COUNT(*) FROM GroupMember WHERE groupId = {groupId}")
    t = cur.fetchall()
    if len(t) > 0:
        memberCount = t[0][0]
    
    ownerUsername = ""
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {owner}")
    t = cur.fetchall()
    if len(t) > 0:
        ownerUsername = decode(t[0][0])
    
    if ownerUsername != "@deleted" and owner != 0:
        cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {abs(owner)}")
        t = cur.fetchall()
        if len(t) > 0:
            ownerUsername = f"<a href='/user/{owner}'><span class='username' style='color:{t[0][1]}'>{ownerUsername}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
        else:
            ownerUsername = f"<a href='/user/{owner}'><span class='username'>{ownerUsername}</span></a>"
    
    cur.execute(f"SELECT question, answer FROM GroupQuestion WHERE groupId = {groupId}")
    d = cur.fetchall()
    da = {}
    for dd in d:
        da[decode(dd[0])] = {"question": decode(dd[0]), "answer": decode(dd[1])}
    ret = []
    for q in sorted(da.keys()):
        ret.append(da[q])
    ret = ret[:10]
    
    return {"success": True, "name": name, "description": description, "ownerUsername": ownerUsername, "memberCount": memberCount, "preview": ret}