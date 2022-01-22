# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import time

from app import app, config
from db import newconn
from functions import *

##########
# Discovery Manage API

@app.post("/api/discovery/publish")
async def apiDiscoveryPublish(request: Request):
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
    
    cur.execute(f"SELECT value FROM Privilege WHERE userId = {userId} AND item = 'mute'")
    t = cur.fetchall()
    if len(t) > 0:
        mute = int(t[0][0])
        if mute == -1 or mute >= int(time.time()):
            return {"success": False, "msg": "You have been muted!"}
        else:
            cur.execute(f"DELETE FROM Privilege WHERE userId = {userId} AND item = 'mute'")
            conn.commit()

    if form["title"] == "" or form["description"] == "":
        return {"success": False, "msg": "Title and description must be filled!"}

    bookId = int(form["bookId"])
    title = encode(form["title"])
    description = encode(form["description"])
    distype = int(form["type"])

    if distype == 1:
        cur.execute(f"SELECT * FROM Discovery WHERE publisherId = {userId} AND bookId = {bookId} AND type = 1")
        if len(cur.fetchall()) != 0:
            return {"success": False, "msg": "Book already published!"}
    elif distype == 2:
        cur.execute(f"SELECT * FROM Discovery WHERE bookId = {bookId} AND type = 2")
        if len(cur.fetchall()) != 0:
            return {"success": False, "msg": "Group already published!"}

    # get share code
    shareCode = ""
    if distype == 1:
        cur.execute(f"SELECT shareCode FROM BookShare WHERE userId = {userId} AND bookId = {bookId} AND shareType = 1")
        t = cur.fetchall()
        if len(t) == 0:
            shareCode = genCode(8)
            cur.execute(f"SELECT shareCode FROM BookShare WHERE shareCode = '{shareCode}'")
            if len(cur.fetchall()) != 0: # conflict
                for _ in range(30):
                    shareCode = genCode(8)
                    cur.execute(f"SELECT shareCode FROM BookShare WHERE shareCode = '{shareCode}'")
                    if len(cur.fetchall()) == 0:
                        break
                cur.execute(f"SELECT shareCode FROM BookShare WHERE shareCode = '{shareCode}'")
                if len(cur.fetchall()) != 0:
                    return {"success": False, "msg": "Unable to generate an unique share code..."}

            cur.execute(f"INSERT INTO BookShare VALUES ({userId}, {bookId}, '{shareCode}', 0, {int(time.time())}, 1)")
            conn.commit()
            shareCode = "!" + shareCode

    elif distype == 2:
        groupId = bookId
        cur.execute(f"SELECT groupCode, owner FROM GroupInfo WHERE groupId = {groupId}")
        t = cur.fetchall()
        if len(t) != 0:
            # check if user is group owner
            if t[0][1] != userId:
                return {"success": False, "msg": "Only the group owner can publish the group on discovery!"}

            shareCode = "@"+t[0][0]
    
        if shareCode == "" or shareCode == "@pvtgroup":
            return {"success": False, "msg": "Group must be open to public before publishing it on Discovery!"}
    
    discoveryId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 6")
    t = cur.fetchall()
    if len(t) > 0:
        discoveryId = t[0][0]
    cur.execute(f"UPDATE IDInfo SET nextId = {discoveryId + 1} WHERE type = 6")
    
    if len(title) >= 256:
        return {"success": False, "msg": "Title too long!"}
    if len(description) >= 2048:
        return {"success": False, "msg": "Description too long!"}

    cur.execute(f"INSERT INTO Discovery VALUES ({discoveryId}, {userId}, {bookId}, '{title}', '{description}', {distype}, 0, 0, 0)")
    conn.commit()

    msg = "Book published to Discovery. People will be able to find it and import it. All your updates made within this book will be synced to Discovery."
    if distype == 2:
        msg = "Group published to Discovery. People will be able to find it and join it. All your updates made within this group will be synced to Discovery."
    
    return {"success": True, "msg": msg, "discoveryId": discoveryId}

@app.post("/api/discovery/unpublish")
async def apiDiscoveryUnpublish(request: Request):
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
    
    discoveryId = int(form["discoveryId"])

    cur.execute(f"SELECT publisherId, bookId FROM Discovery WHERE discoveryId = {discoveryId}")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Post not found!"}
    uid = t[0][0]
    bookId = t[0][1]
    
    # allow admin to unpublish
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        cur.execute(f"SELECT publisherId FROM Discovery WHERE discoveryId = {discoveryId}")
        publisherId = 0
        t = cur.fetchall()
        if len(t) > 0:
            publisherId = t[0][0]
        if publisherId != userId:
            return {"success": False, "msg": "You are not the publisher of this post!"}

    cur.execute(f"DELETE FROM Discovery WHERE discoveryId = {discoveryId}")
    cur.execute(f"DELETE FROM BookShare WHERE userId = {uid} AND bookId = {bookId} AND shareType = 1")
    conn.commit()

    return {"success": True, "msg": "Post unpublished!"}

@app.post("/api/discovery/update")
async def apiDiscoveryUpdate(request: Request):
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
    
    discoveryId = int(form["discoveryId"])
    title = encode(form["title"])
    description = encode(form["description"])

    if form["title"] == "" or form["description"] == "":
        return {"success": False, "msg": "Title and description must be filled!"}

    # allow admin to update
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        cur.execute(f"SELECT publisherId FROM Discovery WHERE discoveryId = {discoveryId}")
        publisherId = 0
        t = cur.fetchall()
        if len(t) > 0:
            publisherId = t[0][0]
        if publisherId != userId:
            return {"success": False, "msg": "You are not the publisher of this post!"}

    if len(title) >= 256:
        return {"success": False, "msg": "Title too long!"}
    if len(description) >= 2048:
        return {"success": False, "msg": "Description too long!"}

    cur.execute(f"UPDATE Discovery SET title = '{title}' WHERE discoveryId = {discoveryId}")
    cur.execute(f"UPDATE Discovery SET description = '{description}' WHERE discoveryId = {discoveryId}")
    conn.commit()
    
    return {"success": True, "msg": "Discovery post updated!"}