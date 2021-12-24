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
# Challenge Mode

rnd=[1,1,1,1,1,1,1,2,2,2,2,2,2,3,3,3,3,3,3,4]
def getChallengeQuestionId(userId, bookId, nofour = False):
    conn = newconn()
    cur = conn.cursor()
    questionId = -1

    # just an interesting random function
    random.shuffle(rnd)
    t = rnd[random.randint(0,len(rnd)-1)]
    while t == 4 and nofour:
        random.shuffle(rnd)
        t = rnd[random.randint(0,len(rnd)-1)]
    
    status1 = getQuestionsInBook(userId, bookId, "status = 1")
    status2 = getQuestionsInBook(userId, bookId, "status = 2")
    
    if t == 1: # tagged question
        cur.execute(f"SELECT questionId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} AND userId = {userId} ORDER BY questionId ASC")
        cd = cur.fetchall()
        questions = []
        
        for dd in status2:
            if (dd[0],) in cd:
                questions.append(dd[0])
            
        if len(questions) != 0:
            questionId = questions[random.randint(0,len(questions) - 1)]

        if questionId == -1:
            t = 2
    
    if t == 2: # questions pending next challenge (already challenged)
        cur.execute(f"SELECT questionId FROM ChallengeData WHERE nextChallenge <= {int(time.time())} AND nextChallenge != 0 AND userId = {userId} ORDER BY nextChallenge ASC")
        cd = cur.fetchall()
        questions = []
        
        for dd in status1:
            if (dd[0],) in cd:
                questions.append(dd[0])
        
        if len(questions) != 0:
            questionId = questions[random.randint(0, len(questions) - 1)]
        
        if questionId == -1:
            t = 3
    
    if t == 3: # questions not challenged before
        cur.execute(f"SELECT questionId FROM ChallengeData WHERE nextChallenge = 0 AND userId = {userId} ORDER BY questionId ASC")
        cd = cur.fetchall()
        questions = []

        for dd in status1:
            if (dd[0],) in cd:
                questions.append(dd[0])
        
        if len(questions) != 0:
            questionId = questions[random.randint(0, len(questions) - 1)]
        
        if questionId == -1:
            t = 5
    
    if t == 5: # questions already challenged (and not pending challenge), but last challenge is 20 minutes ago
        cur.execute(f"SELECT questionId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} AND nextChallenge != 0 AND userId = {userId} ORDER BY nextChallenge ASC")
        cd = cur.fetchall()
        questions = []
        
        for dd in status1:
            if (dd[0],) in cd:
                questions.append(dd[0])
        
        if len(questions) != 0:
            questionId = questions[random.randint(0, len(questions) - 1)]
        
        if questionId == -1:
            t = 4
    
    if t == 4 and not nofour: # deleted question
        d = getQuestionsInBook(userId, bookId, "status = 3")

        if len(d) > 0:
            questionId = d[random.randint(0, len(d) - 1)][0]
        
        else:
            questionId = getChallengeQuestionId(userId, bookId, nofour = True)
    
    return questionId

@app.post("/api/question/challenge/next")
async def apiGetNextChallenge(request: Request):
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

    bookId = int(form["bookId"])
    questionId = getChallengeQuestionId(userId, bookId)
    mixcnt = int(form["mixcnt"])

    if questionId == -1:
        mix = []
        for _ in range(mixcnt):
            mix.append({"question": "No more challenge", "answer": "No more challenge"})
        return {"success": True, "questionId": questionId, "question": "No more challenge", "answer": "No more challenge", "status": 1, "mix": mix}

    cur.execute(f"SELECT question, answer, status FROM QuestionList WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    (question, answer, status) = d[0]
    question = decode(question)
    answer = decode(answer)

    mix = []
    qs = list(getQuestionsInBook(userId, bookId, "status >= 0"))
    while len(qs) <= mixcnt:
        qs.append((-1,encode("No more choice"),encode("No more choice")))
    for _ in range(mixcnt):
        random.shuffle(qs)
    for i in range(mixcnt):
        mix.append({"question": decode(qs[i][1]), "answer": decode(qs[i][2])})

    return {"success": True, "questionId": questionId, "question": question, "answer": answer, "status": status, "mix": mix}

# addtime = [20 minute, 1 hour, 3 hour, 8 hour, 1 day, 2 day, 5 day, 10 day]
addtime = [300, 1200, 3600, 10800, 28800, 86401, 172800, 432000, 864010]
@app.post("/api/question/challenge/update")
async def apiUpdateChallengeRecord(request: Request):
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
    memorized = int(form["memorized"])
    getNext = int(form["getNext"])
    ts = int(time.time())

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE questionId = {questionId} AND userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()

    if questionId != -1:
        cur.execute(f"INSERT INTO ChallengeRecord VALUES ({userId}, {questionId}, {memorized}, {ts})")
        cur.execute(f"UPDATE ChallengeData SET lastChallenge = {ts} WHERE questionId = {questionId}  AND userId = {userId}")

        tot = 0
        if memorized == 1:
            tot = 1
            for dd in d:
                if dd[0] == 1:
                    tot += 1
            if tot > 8:
                tot = 8
            cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[tot]} WHERE questionId = {questionId} AND userId = {userId}")

        elif memorized == 0:
            cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[0]} WHERE questionId = {questionId} AND userId = {userId}")
    
    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE questionId = {questionId} AND userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()

    s = []
    s.append(0)
    i = 1
    for dd in d:
        if dd[0] == 1:
            s.append(s[i-1] + 1)
        else:
            s.append(0)
        i += 1
    for i in range(0,len(s)):
        if s[i] >= 2:
            cur.execute(f"SELECT memorizedTimestamp FROM QuestionList WHERE userId = {userId} AND questionId = {questionId}")
            t = cur.fetchall()
            if len(t) != 0 and t[0][0] == 0:
                cur.execute(f"UPDATE QuestionList SET memorizedTimestamp = {int(time.time())} WHERE userId = {userId} AND questionId = {questionId}")

                books = getBookId(userId, questionId)
                for bookId in books:
                    cur.execute(f"SELECT progress FROM Book WHERE bookId = {bookId} AND userId = {userId}")
                    p = cur.fetchall()
                    if len(p) > 0:
                        cur.execute(f"UPDATE Book SET progress = progress + 1 WHERE bookId = {bookId} AND userId = {userId}")

    conn.commit()

    if getNext == 1:
        bookId = int(form["bookId"])
        mixcnt = int(form["mixcnt"])

        questionId = getChallengeQuestionId(userId, bookId)

        if questionId == -1:
            mix = []
            for _ in range(mixcnt):
                mix.append({"question": "No more challenge", "answer": "No more challenge"})
            return {"success": True, "questionId": questionId, "question": "No more challenge", "answer": "No more challenge", "status": 1, "mix": mix}

        cur.execute(f"SELECT question, answer, status FROM QuestionList WHERE questionId = {questionId} AND userId = {userId}")
        d = cur.fetchall()
        (question, answer, status) = d[0]
        question = decode(question)
        answer = decode(answer)

        mix = []
        qs = list(getQuestionsInBook(userId, bookId, "status >= 0"))
        while len(qs) <= mixcnt:
            qs.append((-1,encode("No more choice"),encode("No more choice")))
        for _ in range(mixcnt):
            random.shuffle(qs)
        for i in range(mixcnt):
            mix.append({"question": decode(qs[i][1]), "answer": decode(qs[i][2])})

        return {"success": True, "questionId": questionId, "question": question, "answer": answer, "status": status, "mix": mix}

    else:
        return {"success": True}