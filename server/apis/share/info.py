# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import time

from app import app, config
from db import newconn
from functions import *

##########
# Share API
# Info

@app.post("/api/share/preview")
async def apiSharePreview(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    
    shareCode = form["shareCode"]

    if shareCode.startswith("!"):
        shareCode = shareCode[1:]
    
    if not shareCode.isalnum():
        return {"success": False, "msg": "Invalid share code!"}

    cur.execute(f"SELECT userId, bookId, importCount FROM BookShare WHERE shareCode = '{shareCode}'")
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Invalid share code!"}
    d = d[0]
    
    sharerUserId = d[0]
    bookId = d[1]
    importCount = d[2]
    
    sharerUsername = ""
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {sharerUserId}")
    t = cur.fetchall()
    if len(t) > 0:
        sharerUsername = decode(t[0][0])
    
    if sharerUsername != "@deleted" and sharerUserId != 0:
        cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {abs(sharerUserId)}")
        t = cur.fetchall()
        if len(t) > 0:
            sharerUsername = f"<a href='/user/{sharerUserId}'><span class='username' style='color:{t[0][1]}'>{sharerUsername}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
        else:
            sharerUsername = f"<a href='/user/{sharerUserId}'><span class='username'>{sharerUsername}</span></a>"

    name = encode(sharerUsername + "'s book")
    if bookId != 0:
        name = "Unknown Book"
        cur.execute(f"SELECT name FROM Book WHERE userId = {sharerUserId} AND bookId = {bookId}")
        tt = cur.fetchall()
        if len(tt) > 0:
            name = tt[0][0]
            
    if bookId != 0:
        t = getBookData(sharerUserId, bookId)
    else:
        cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {sharerUserId}")
        ttt = cur.fetchall()
        for tt in ttt:
            t.append(tt[0])
    
    da = {}
    for tt in t:
        cur.execute(f"SELECT question, answer FROM QuestionList WHERE userId = {sharerUserId} AND questionId = {tt}")
        b = cur.fetchall()
        bb = b[0]
        da[decode(bb[0])] = {"question": decode(bb[0]), "answer": decode(bb[1])}
    ret = []
    for q in sorted(da.keys()):
        ret.append(da[q])
    ret = ret[:10]
    
    return {"success": True, "name": decode(name), "sharerUsername": sharerUsername, "importCount": importCount, "preview": ret}