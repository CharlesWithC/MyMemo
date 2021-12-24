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
# Discovery Engage API

@app.post("/api/discovery/pin")
async def apiDiscoveryPin(request: Request):
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

    # only admin can pin
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        return {"success": False, "msg": "Only admins are allowed to pin / unpin discovery posts!"}
    
    op = form["operation"]
    discoveryId = int(form["discoveryId"])

    if op == "pin":
        cur.execute(f"SELECT pin FROM Discovery WHERE discoveryId = {discoveryId}")
        t = cur.fetchall()
        if len(t) > 0:
            if t[0][0] == 0:
                cur.execute(f"UPDATE Discovery SET pin = 1 WHERE discoveryId = {discoveryId}")
                conn.commit()
                return {"success": True, "msg": "Pinned!"}
            else:
                return {"success": False, "msg": "Post already pinned!"}
        else:
            return {"success": False, "msg": "Post not found!"}

    elif op == "unpin":
        cur.execute(f"SELECT pin FROM Discovery WHERE discoveryId = {discoveryId}")
        t = cur.fetchall()
        if len(t) > 0:
            if t[0][0] == 1:
                cur.execute(f"UPDATE Discovery SET pin = 0 WHERE discoveryId = {discoveryId}")
                conn.commit()
                return {"success": True, "msg": "Unpinned!"}
            else:
                return {"success": False, "msg": "Post not pinned!"}
        else:
            return {"success": False, "msg": "Post not found!"}

@app.post("/api/discovery/like")
async def apiDiscoveryLike(request: Request):
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
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Post not found!"}
    
    cur.execute(f"SELECT * FROM DiscoveryLike WHERE discoveryId = {discoveryId} AND userId = {userId} AND likes = 1")
    if len(cur.fetchall()) != 0:
        cur.execute(f"DELETE FROM DiscoveryLike WHERE discoveryId = {discoveryId} AND userId = {userId} AND likes = 1")
        conn.commit()
        return {"success": True, "msg": "Unliked!", "liked": False}
    else:
        cur.execute(f"INSERT INTO DiscoveryLike VALUES ({discoveryId}, {userId}, 1)")
        conn.commit()
        return {"success": True, "msg": "Liked!", "liked": True}