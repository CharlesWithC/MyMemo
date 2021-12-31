# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import os, sys, time, math
import json, requests

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Discovery Info API

@app.get("/api/discovery")
@app.post("/api/discovery")
async def apiDiscovery(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()

    toplist = json.loads(requests.post(f"http://{config.search_server_ip}:{config.search_server_port}/search/discoveryTop").text)["top"]
    top = []

    for t in toplist:
        cur.execute(f"SELECT discoveryId, title, description, publisherId, type, bookId, pin FROM Discovery WHERE discoveryId = {t}")
        d = cur.fetchall()
        if len(d) == 0:
            continue
        dd = d[0]
        if dd[4] == 1:
            cur.execute(f"SELECT shareCode FROM BookShare WHERE bookId = {dd[5]} AND shareType = 1")
            if len(cur.fetchall()) == 0:
                continue
        elif dd[4] == 2:
            cur.execute(f"SELECT groupCode FROM GroupInfo WHERE groupId = {dd[5]}")
            p = cur.fetchall()
            if len(p) > 0:
                if p[0][0] == '' or p[0][0] == '@pvtgroup':
                    continue
            else:
                continue
        
        if checkBanned(dd[3]): # display nothing from banned user
            continue

        publisher = "Unknown User"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) != 0:
            publisher = decode(t[0][0])
            if publisher == "@deleted":
                publisher = "Deleted Account"

        # update views
        cur.execute(f"SELECT views FROM Discovery WHERE discoveryId = {dd[0]}")
        views = 0
        t = cur.fetchall()
        if len(t) > 0:
            views = t[0][0]
        
        # get views and likes
        cur.execute(f"SELECT COUNT(likes) FROM DiscoveryLike WHERE discoveryId = {dd[0]}")
        likes = 0
        t = cur.fetchall()
        if len(t) > 0:
            likes = t[0][0]

        # get imports / members
        imports = 0
        if dd[4] == 1:
            cur.execute(f"SELECT importCount FROM BookShare WHERE userId = {dd[3]} AND bookId = {dd[5]} AND shareType = 1")
            t = cur.fetchall()
            if len(t) > 0:
                imports = t[0][0]
        elif dd[4] == 2:
            cur.execute(f"SELECT COUNT(*) FROM GroupMember WHERE groupId = {dd[5]}")
            t = cur.fetchall()
            if len(t) > 0:
                imports = t[0][0]
        
        pinned = dd[6]
        
        cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) > 0:
            publisher = f"<a href='/user?userId={dd[3]}'><span class='username' style='color:{t[0][1]}'>{publisher}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
        else:
            publisher = f"<a href='/user?userId={dd[3]}'><span class='username'>{publisher}</span></a>"

        top.append({"discoveryId": dd[0], "title": decode(dd[1]), "description": decode(dd[2]), \
            "publisher": publisher, "type": dd[4], "views": views, "likes": likes, "imports": imports, "pinned": pinned})

    page = int(form["page"])
    if page <= 0:
        page = 1

    pageLimit = int(form["pageLimit"])
    if pageLimit <= 0:
        pageLimit = 20
    
    if pageLimit > 100:
        return {"success": True, "data": [], "total": 0}

    orderBy = form["orderBy"] # title / publisher / views / likes NOTE: pin should stick on top
    if not orderBy in ["none", "title", "publisher", "views", "likes"]:
        orderBy = "title"

    order = form["order"]
    if not order in ["asc", "desc"]:
        order = "asc"
    l = {"asc": 0, "desc": 1}
    order = l[order]

    search = form["search"]

    d = json.loads(requests.post(f"http://{config.search_server_ip}:{config.search_server_port}/search/discovery", data = {"search": search}).text)["result"]
    if len(d) == 0:
        return {"success": True, "data": [], "total": 0, "toplist": top}

    dis = []
    for dd in d:
        if dd[4] == 1:
            cur.execute(f"SELECT shareCode FROM BookShare WHERE bookId = {dd[5]} AND shareType = 1")
            if len(cur.fetchall()) == 0:
                continue
        elif dd[4] == 2:
            cur.execute(f"SELECT groupCode FROM GroupInfo WHERE groupId = {dd[5]}")
            p = cur.fetchall()
            if len(p) > 0:
                if p[0][0] == '' or p[0][0] == '@pvtgroup':
                    continue
            else:
                continue
        
        if checkBanned(dd[3]): # display nothing from banned user
            continue

        publisher = "Unknown User"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) != 0:
            publisher = decode(t[0][0])
            if publisher == "@deleted":
                publisher = "Deleted Account"

        # update views
        cur.execute(f"SELECT views FROM Discovery WHERE discoveryId = {dd[0]}")
        views = 0
        t = cur.fetchall()
        if len(t) > 0:
            views = t[0][0]
        
        # get views and likes
        cur.execute(f"SELECT COUNT(likes) FROM DiscoveryLike WHERE discoveryId = {dd[0]}")
        likes = 0
        t = cur.fetchall()
        if len(t) > 0:
            likes = t[0][0]

        # get imports / members
        imports = 0
        if dd[4] == 1:
            cur.execute(f"SELECT importCount FROM BookShare WHERE userId = {dd[3]} AND bookId = {dd[5]} AND shareType = 1")
            t = cur.fetchall()
            if len(t) > 0:
                imports = t[0][0]
        elif dd[4] == 2:
            cur.execute(f"SELECT COUNT(*) FROM GroupMember WHERE groupId = {dd[5]}")
            t = cur.fetchall()
            if len(t) > 0:
                imports = t[0][0]
        
        pinned = dd[6]
        
        cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) > 0:
            publisher = f"<a href='/user?userId={dd[3]}'><span class='username' style='color:{t[0][1]}'>{publisher}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
        else:
            publisher = f"<a href='/user?userId={dd[3]}'><span class='username'>{publisher}</span></a>"

        dis.append({"discoveryId": dd[0], "title": decode(dd[1]), "description": decode(dd[2]), \
            "publisher": publisher, "type": dd[4], "views": views, "likes": likes, "imports": imports, "pinned": pinned})

    t = {}
    ret = []
    for dd in dis:
        if dd["pinned"]:
            if order == 0:
                ret.append(dd) # put them on top
            continue

        if orderBy == "title" or orderBy == "none":
            t[dd["title"] + "<id>" + str(dd["discoveryId"])] = dd
        elif orderBy == "publisher":
            t[dd["publisher"] + dd["title"] + "<id>" + str(dd["discoveryId"])] = dd
        elif orderBy == "views":
            t[str(dd["views"]) + dd["title"] + "<id>" + str(dd["discoveryId"])] = dd
        elif orderBy == "likes":
            t[str(dd["likes"]) + dd["title"] + "<id>" + str(dd["discoveryId"])] = dd
    
    if orderBy != "none":
        for key in sorted(t.keys()):
            ret.append(t[key])
    else:
        for key in t.keys():
            ret.append(t[key])
        
    if order == 1:
        for dd in dis:
            if dd["pinned"]:
                ret.append(dd)
        ret = ret[::-1]
    
    dis = ret

    page = int(form["page"])
    pageLimit = int(form["pageLimit"])
    
    if len(dis) <= (page - 1) * pageLimit:
        return {"success": True, "data": [], "total": (len(dis) - 1) // pageLimit + 1, "totalD": len(dis), "toplist": top}
    elif len(dis) <= page * pageLimit:
        return {"success": True, "data": dis[(page - 1) * pageLimit :], "total": (len(dis) - 1) // pageLimit + 1, "totalD": len(dis), "toplist": top}
    else:
        return {"success": True, "data": dis[(page - 1) * pageLimit : page * pageLimit], "total": (len(dis) - 1) // pageLimit + 1, "totalD": len(dis), "toplist": top}

@app.get("/api/discovery/{discoveryId:int}")
@app.post("/api/discovery/{discoveryId:int}")
async def apiDiscoveryData(discoveryId: int, request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()

    userId = 0

    if request.method == "POST":
        loggedin = False
        if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
            loggedin = False
        else:
            loggedin = True
        
        if loggedin:
            loggedin = False
            userId = int(form["userId"])
            token = form["token"]
            if validateToken(userId, token):
                loggedin = True
        
        if not loggedin:
            userId = 0
    
    cur.execute(f"SELECT publisherId, bookId, title, description, type, pin FROM Discovery WHERE discoveryId = {discoveryId}")
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Post not found!"}
    d = d[0]

    uid = d[0]
    bookId = d[1]
    title = decode(d[2])
    description = decode(d[3])
    distype = d[4]
    pinned = d[5]

    if checkBanned(uid):
        return {"success": False, "msg": "Post not found!"}
    
    # Check share existence
    if distype == 1:
        cur.execute(f"SELECT * FROM Book WHERE userId = {uid} AND bookId = {bookId}")
        t = cur.fetchall()
        if len(t) == 0:
            cur.execute(f"DELETE FROM Discovery WHERE discoveryId = {discoveryId}")
            conn.commit()
            return {"success": False, "msg": "Book not found!"}
    
    elif distype == 2:
        cur.execute(f"SELECT * FROM GroupInfo WHERE groupId = {bookId}")
        t = cur.fetchall()
        if len(t) == 0:
            cur.execute(f"DELETE FROM Discovery WHERE discoveryId = {discoveryId}")
            conn.commit()
            return {"success": False, "msg": "Group not found!"}

    
    # Check share status as books must be shared before being imported
    # Do not clear discovery status as publisher may just want to close it temporarily
    shareCode = ""
    if distype == 1:
        cur.execute(f"SELECT shareCode FROM BookShare WHERE userId = {uid} AND bookId = {bookId} AND shareType = 1")
        t = cur.fetchall()
        if len(t) != 0:
            shareCode = "!"+t[0][0]

        if shareCode == "":
            return {"success": False, "msg": "Book not found!"}

    elif distype == 2:
        cur.execute(f"SELECT groupCode FROM GroupInfo WHERE groupId = {bookId}")
        t = cur.fetchall()
        if len(t) != 0:
            shareCode = "@"+t[0][0]

        if shareCode == "" or shareCode == "@pvtgroup":
            return {"success": False, "msg": "Group not open to public! Maybe the publisher just closed it temporarily."}

    # Get discovery publisher username
    publisher = "Unknown User"
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) != 0:
        publisher = decode(t[0][0])
        if publisher == "@deleted":
            publisher = "Deleted Account"
    
    isPublisher = False
    if uid == userId:
        isPublisher = True
    
    # get questions
    qt = {}
    questions = []
    if distype == 1:
        p = getBookData(uid, bookId)
        for pp in p:
            cur.execute(f"SELECT question, answer FROM QuestionList WHERE userId = {uid} AND questionId = {pp}")
            t = cur.fetchall()
            if len(t) == 0:
                continue
            qt[decode(t[0][0]) + "<id>" + str(pp)] = {"question": decode(t[0][0]), "answer": decode(t[0][1])}
    elif distype == 2:
        cur.execute(f"SELECT question, answer FROM GroupQuestion WHERE groupId = {bookId}")
        t = cur.fetchall()
        i = 0
        for tt in t:
            i += 1
            qt[decode(tt[0]) + "<id>" + str(i)] = {"question": decode(tt[0]), "answer": decode(tt[1])}
    qcnt = 0
    for key in sorted(qt.keys()):
        qcnt += 1
        if qcnt > 20:
            break
        questions.append(qt[key])

    # update views
    cur.execute(f"SELECT views FROM Discovery WHERE discoveryId = {discoveryId}")
    views = 1
    t = cur.fetchall()
    if len(t) > 0:
        views = t[0][0] + 1
        cur.execute(f"UPDATE Discovery SET views = views + 1 WHERE discoveryId = {discoveryId}")
        conn.commit()
    
    # get views and likes
    cur.execute(f"SELECT COUNT(likes) FROM DiscoveryLike WHERE discoveryId = {discoveryId}")
    likes = 0
    t = cur.fetchall()
    if len(t) > 0:
        likes = t[0][0]
    
    # get user liked
    cur.execute(f"SELECT likes FROM DiscoveryLike WHERE discoveryId = {discoveryId} AND userId = {userId}")
    liked = False
    t = cur.fetchall()
    if len(t) > 0:
        liked = True
    
    # get imports / members
    imports = 0
    if distype == 1:
        cur.execute(f"SELECT importCount FROM BookShare WHERE userId = {uid} AND bookId = {bookId} AND shareType = 1")
        t = cur.fetchall()
        if len(t) > 0:
            imports = t[0][0]
    elif distype == 2:
        cur.execute(f"SELECT COUNT(*) FROM GroupMember WHERE groupId = {bookId}")
        t = cur.fetchall()
        if len(t) > 0:
            imports = t[0][0]

    cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) > 0:
        publisher = f"<a href='/user?userId={uid}'><span class='username' style='color:{t[0][1]}'>{publisher}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
    else:
        publisher = f"<a href='/user?userId={uid}'><span class='username'>{publisher}</span></a>"

    return {"success": True, "title": title, "description": description, "questions": questions, \
        "shareCode": shareCode, "type": distype, "publisher": publisher, "isPublisher": isPublisher, \
            "views": views, "likes": likes, "liked": liked, "imports": imports, "pinned": pinned}