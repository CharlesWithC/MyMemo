# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import os, sys, datetime, time
import random
import json

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Question API
# Practice Mode

@app.post("/api/question/next")
async def apiGetNext(request: Request):
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

    questionId = -1

    op = {-1: "<", 1: ">"}
    order = {-1: "DESC", 1: "ASC"}
    moveType = int(form["moveType"]) # -1: previous, 1: next, 0: random
    if moveType in [-1,1]:
        op = op[moveType]
        order = order[moveType]

    current = -1
    if moveType in [-1, 1]:
        current = int(form["questionId"])

    statusRequirement = {1: "status = 1 OR status = 2", 2: "status = 2", 3: "status = 3"}
    status = int(form["status"])
    statusRequirement = statusRequirement[status]

    bookId = int(form["bookId"])
    
    if bookId == 0:
        if moveType in [-1,1]:
            cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE questionId{op}{current} AND ({statusRequirement}) AND userId = {userId} ORDER BY questionId {order} LIMIT 1")
            d = cur.fetchall()
            if len(d) == 0: # no matching results, then find result from first / end
                cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE ({statusRequirement}) AND userId = {userId} ORDER BY questionId {order} LIMIT 1")
                d = cur.fetchall()

        elif moveType == 0:
            cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE ({statusRequirement}) AND userId = {userId} ORDER BY RAND() LIMIT 1")
            d = cur.fetchall()
    
    else:
        d = getQuestionsInBook(userId, bookId, statusRequirement)
        if len(d) != 0:
            if moveType == -1:
                lst = d[-1]
                for dd in d:
                    if dd[0] == current:
                        break
                    lst = dd
                d = [lst]

            elif moveType == 1:
                nxt = d[0]
                ok = False
                for dd in d:
                    if ok is True:
                        nxt = dd
                        break
                    if dd[0] == current:
                        ok = True
                d = [nxt]
            
            elif moveType == 0:
                rnd = random.randint(0,len(d)-1)
                d = [d[rnd]]

    if len(d) == 0:
        return {"success": True, "questionId": -1, "question": "[No more question]", "answer": "Maybe change the settings?\nOr check your connection?", "status": 1}

    (questionId, question, answer, status) = d[0]
    question = decode(question)
    answer = decode(answer)

    return {"success": True, "questionId": questionId, "question": question, "answer": answer, "status": status}