# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import datetime, time
import random

from app import app, config
from db import newconn
from functions import *

##########
# Question API
# Info

@app.post("/api/question")
async def apiGetQuestion(request: Request):
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
    
    cur.execute(f"SELECT * FROM Challenge WHERE userId = {userId} AND expire >= {int(time.time())}")
    if len(cur.fetchall()) != 0:
        return {"success": False, "msg": "An ongoing challenge is detected, you cannot start another mode by the time!"}
    
    questionId = int(form["questionId"])
    
    cur.execute(f"SELECT question, answer, status FROM QuestionList WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()

    if len(d) == 0:
        raise HTTPException(status_code=404)
    
    (question, answer, status) = d[0]
    question = decode(question)
    answer = decode(answer)

    return {"success": True, "questionId": questionId, "question":question, "answer": answer, "status": status}

@app.post("/api/question/id")
async def apiGetQuestionID(request: Request):
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
        
    cur.execute(f"SELECT * FROM Challenge WHERE userId = {userId} AND expire >= {int(time.time())}")
    if len(cur.fetchall()) != 0:
        return {"success": False, "msg": "An ongoing challenge is detected, you cannot start another mode by the time!"}
    
    question = form["question"].replace("\n","\\n")
    bookId = int(form["bookId"])
    bookData = getBookData(userId, bookId)

    if question == "":
        cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) == 0:
            raise HTTPException(status_code=404)
        
        l = []
        for dd in d:
            if bookId == 0 or dd[0] in bookData:
                l.append(dd[0])
        random.shuffle(l)

        if len(l) == 0:
            raise HTTPException(status_code=404)

        return {"success": True, "questionId": l[0]}
    
    else:
        cur.execute(f"SELECT questionId FROM QuestionList WHERE question = '{encode(question)}' AND userId = {userId}")
        d = cur.fetchall()
        if len(d) == 0:
            raise HTTPException(status_code=404)
            
        for dd in d:
            questionId = dd[0]
            if bookId > 0 and not questionId in bookData:
                continue

            # If there are multiple records, then return the first one
            # The user is warned when they try to insert multiple records with the same question
            return {"success": True, "questionId" : questionId}

@app.post("/api/question/stat")
async def apiGetQuestionStat(request: Request):
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
    
    questionId = int(form["questionId"])
    cur.execute(f"SELECT question FROM QuestionList WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        raise HTTPException(status_code=404)
    question = decode(d[0][0])
    
    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE questionId = {questionId} AND updateTo <= 0 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        raise HTTPException(status_code=404)
    d = d[0]
    astatus = d[0] # how it is added
    ats = d[1] # addition timestamp

    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()

    status = 1

    tagcnt = 0
    lsttag = 0
    untagcnt = 0
    lstuntag = 0

    delcnt = 0
    lstdel = 0
    undelcnt = 0
    lstundel = 0

    lastEdit = 0
    lastGroupEdit = 0

    for i in range(0, len(d)):
        if status == 1 and d[i][0] == 2:
            tagcnt += 1
            lsttag = d[i][1]
        elif status == 2 and d[i][0] == 1:
            untagcnt += 1
            lstuntag = d[i][1]
        elif status == 1 and d[i][0] == 3:
            delcnt += 1
            lstdel = d[i][1]
        elif status == 3 and d[i][0] == 1:
            undelcnt += 1
            lstundel = d[i][1]
        elif d[i][0] == 100 and d[i][1] >= lastEdit:
            lastEdit = d[i][1]
        elif d[i][0] == 101 and d[i][1] >= lastGroupEdit:
            lastGroupEdit = d[i][1]

        status = d[i][0]
    
    cur.execute(f"SELECT nextChallenge, lastChallenge FROM ChallengeData WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        raise HTTPException(status_code=404)
    d = d[0]
    nxt = d[0]
    lst = d[1]

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    appeared = len(d)
    mem = 0
    lstmem = 0
    fgt = 0
    lstfgt = 0
    for dd in d:
        if dd[0] == 1:
            mem += 1
            lstmem = dd[1]
        elif dd[0] == 0:
            fgt += 1
            lstfgt = dd[1]
    lst30d = 0
    lst30dmem = 0
    lst7d = 0
    lst7dmem = 0
    lst1d = 0
    lst1dmem = 0
    for dd in d:
        if (time.time() - dd[1]) <= 86401*30:
            lst30d += 1
            lst30dmem += dd[0]
        if (time.time() - dd[1]) <= 86401*7:
            lst7d += 1
            lst7dmem += dd[0]
        if (time.time() - dd[1]) <= 86401:
            lst1d += 1
            lst1dmem += dd[0]
    
    def ts2dt(ts):
        return f"<time>{ts}</time>"
        #return datetime.datetime.fromtimestamp(ts)

    res = f"About {question}\n"

    if astatus == 0:
        res += f"Added by magic (unknown adding method).\n"
    elif astatus == -1:
        res += f"Imported from file.\n"  
    elif astatus == -2:
        res += f"Added at {ts2dt(ats)} on website.\n"  
    elif astatus == -3:
        res += f"Imported from a group's book.\n"
    
    if lastEdit != 0 and lastGroupEdit == 0:
        res += f"Last edited at <time>{ts2dt(lastEdit)}</time>.\n"
    elif lastGroupEdit != 0 and lastEdit >= lastGroupEdit:
        res += f"Last edited at <time>{ts2dt(lastEdit)}</time> by you and synced to other members in group.\n"
    elif lastGroupEdit != 0 and lastEdit < lastGroupEdit:
        res += f"Last edited at <time>{ts2dt(lastGroupEdit)}</time> by an editor in group.\n"

    if tagcnt > 0:
        res += f"Tagged for {tagcnt} times\n(Last time: {ts2dt(lsttag)}),\n"
    else:
        res += f"Never tagged,\n"
    if delcnt > 0:
        res += f"Deleted for {delcnt} times\n(Last time: {ts2dt(lstdel)}).\n"
    else:
        res += f"Never deleted.\n"

    res += "\n"

    res += "In Challenge Mode,\n"
    if appeared > 0:
        res += f"It has appeared for {appeared} times,\n"
        if mem > 0:
            if fgt == 0:
                res += f"You remembered it every time. Good job!\n"
            else:
                res += f"While recorded as memorized for {mem} times,\n"
                if fgt > 0:
                    res += f"And recorded as forgotten for {fgt} times.\n"
        else:
            res += f"You never memorized it.\n"
        
        res += "\n"

        # res += f"In the last 30 days,"
        # if lst30d > 0:
        #     res += f"it appeared {lst30d} times\nAnd you remembered it for {lst30dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        # if lst7d > 0:
        #     res += f"it appeared {lst7d} times\nAnd you remembered it for {lst7dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        # if lst1d > 0:
        #     res += f"it appeared {lst1d} times\nAnd you remembered it for {lst1dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        
        res += f"The last time it appeared is at\n{ts2dt(lst)},\n"
        if lstmem < lstfgt:
            res += "And you forgot it that time.\n"
        else:
            res += "And you remembered it that time.\n"

        res += "\n"

        res += f"Normally, it will appear again at around\n{ts2dt(nxt)},\n"
        res += f"If you do Challenge Mode at that time.\n"

        res += "\n"
        res += "[Time in UTC + 0]"

    else:
        res += f"It hasn't appeared yet."
    
    return {"success": True, "msg": res}

@app.post("/api/question/count")
async def apiGetQuestionCount(request: Request):
    ip = request.client.host
    form = await request.form()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)

    return {"success": True, "count": str(getQuestionCount(userId))}