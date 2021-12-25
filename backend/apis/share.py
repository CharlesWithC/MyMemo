# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import os, sys, time
import json

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Share API

@app.post("/api/share")
async def apiShareBook(request: Request):
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

    if op == "list":
        page = int(form["page"])
        if page <= 0:
            page = 1

        pageLimit = int(form["pageLimit"])
        if pageLimit <= 0:
            pageLimit = 20
        
        if pageLimit > 100:
            return {"success": True, "data": [], "total": 0}

        orderBy = form["orderBy"]
        if not orderBy in ["name", "shareCode", "importCount", "timestamp"]:
            orderBy = "name"

        order = form["order"]
        if not order in ["asc", "desc"]:
            order = "asc"
        l = {"asc": 0, "desc": 1}
        order = l[order]

        search = form["search"]

        ret = []
        i2n = {}
        cur.execute(f"SELECT bookId, shareCode, importCount, createTS FROM BookShare WHERE userId = {userId} AND shareType = 0")
        d = cur.fetchall()
        for dd in d:
            name = ""
            if dd[0] in i2n.keys():
                name = i2n[dd[0]]
            else:
                cur.execute(f"SELECT name FROM Book WHERE bookId = {dd[0]}")
                t = cur.fetchall()
                if len(t) == 0:
                    continue
                name = decode(t[0][0])
                i2n[dd[0]] = name
            
            ret.append({"bookId": dd[0], "name": name, "shareCode": "!" + dd[1], "importCount": dd[2], "timestamp": dd[3]})
        
        t = {}
        i = 0
        for dd in ret:
            ok = False
            for tt in dd.keys():
                if search == "" or search in str(dd[tt]):
                    ok = True
                    break
            if not ok:
                continue
            i += 1
            t[str(dd[orderBy]) + str(dd["bookId"]) + str(i)] = dd
            
        ret = []
        for key in sorted(t.keys()):
            ret.append(t[key])
        if order == 1:
            ret = ret[::-1]

        if len(ret) <= (page - 1) * pageLimit:
            return {"success": True, "data": [], "total": (len(ret) - 1) // pageLimit + 1, "totalShare": len(ret)}
        elif len(ret) <= page * pageLimit:
            return {"success": True, "data": ret[(page - 1) * pageLimit :], "total": (len(ret) - 1) // pageLimit + 1, "totalShare": len(ret)}
        else:
            return {"success": True, "data": ret[(page - 1) * pageLimit : page * pageLimit], "total": (len(ret) - 1) // pageLimit + 1, "totalShare": len(ret)}

    elif op == "create":
        bookId = int(form["bookId"])

        cur.execute(f"SELECT * FROM Book WHERE userId = {userId} AND bookId = {bookId}")
        if len(cur.fetchall()) == 0:
            return {"success": False, "msg": "Book not found!"}
        
        cur.execute(f"SELECT shareCode FROM BookShare WHERE userId = {userId} AND bookId = {bookId} AND shareType = 0")
        t = cur.fetchall()
        if len(t) >= 20:
            return {"success": False, "msg": "You can create at most 20 shares for one book!"}
        else:
            shareCode = genCode(8)
            cur.execute(f"SELECT shareCode FROM BookShare WHERE shareCode = '{shareCode}'")
            if len(cur.fetchall()) != 0: # conflict
                for _ in range(30):
                    shareCode = genCode(8)
                    cur.execute(f"SELECT shareCode FROM Book WHERE shareCode = '{shareCode}'")
                    if len(cur.fetchall()) == 0:
                        break
                cur.execute(f"SELECT shareCode FROM Book WHERE shareCode = '{shareCode}'")
                if len(cur.fetchall()) != 0:
                    return {"success": False, "msg": "Unable to generate an unique share code..."}
                    
            cur.execute(f"INSERT INTO BookShare VALUES ({userId}, {bookId}, '{shareCode}', 0, {int(time.time())}, 0)")
            conn.commit()

            return {"success": True, "msg": "A new book share has been created!", "shareCode": "!" + shareCode}

    elif op == "remove":
        code = form["shareCode"]
        code = code.replace("!","").replace("@","")

        if not code.isalnum():
            return {"success": False, "msg": "Invalid share code!"}

        cur.execute(f"SELECT bookId FROM BookShare WHERE userId = {userId} AND shareType = 0 AND shareCode = '{code}'")
        t = cur.fetchall()
        if len(t) == 0:
            return {"success": False, "msg": "Invalid share code!"}
        else:
            cur.execute(f"DELETE FROM BookShare WHERE userId = {userId} AND bookId = {t[0][0]} AND shareCode = '{code}'")
            conn.commit()
            return {"success": True, "msg": "Book unshared!"}