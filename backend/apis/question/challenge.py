# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, datetime, time
import random
import json

from app import app, config
import db
from functions import *
import sessions

import MySQLdb
import sqlite3
conn = None

def updateconn():
    global conn
    if config.database == "mysql":
        conn = MySQLdb.connect(host = app.config["MYSQL_HOST"], user = app.config["MYSQL_USER"], \
            passwd = app.config["MYSQL_PASSWORD"], db = app.config["MYSQL_DB"])
    elif config.database == "sqlite":
        conn = sqlite3.connect("database.db", check_same_thread = False)
    
updateconn()

##########
# Question API
# Challenge Mode

rnd=[1,1,1,1,1,1,1,2,2,2,2,2,2,3,3,3,3,3,3,4]
def getChallengeQuestionId(userId, bookId, nofour = False):
    updateconn()
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

@app.route("/api/question/challenge/next", methods = ['POST'])
def apiGetNextChallenge():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    bookId = int(request.form["bookId"])
    questionId = getChallengeQuestionId(userId, bookId)

    if questionId == -1:
        return json.dumps({"questionId": questionId, "question": "Out of challenge", "answer": "You are super!\nNo more challenge can be done!", "status": 1})

    cur.execute(f"SELECT question, answer, status FROM QuestionList WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    (question, answer, status) = d[0]
    question = decode(question)
    answer = decode(answer)

    mixcnt = int(request.form["mixcnt"])
    mix = []
    qs = list(getQuestionsInBook(userId, bookId, "status >= 0"))
    for _ in range(mixcnt):
        random.shuffle(qs)
    for i in range(mixcnt):
        mix.append({"question": decode(qs[i][1]), "answer": decode(qs[i][2])})

    return json.dumps({"questionId": questionId, "question": question, "answer": answer, "status": status, "mix": mix})

# addtime = [20 minute, 1 hour, 3 hour, 8 hour, 1 day, 2 day, 5 day, 10 day]
addtime = [300, 1200, 3600, 10800, 28800, 86401, 172800, 432000, 864010]
@app.route("/api/question/challenge/update", methods = ['POST'])
def apiUpdateChallengeRecord():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    questionId = int(request.form["questionId"])
    memorized = int(request.form["memorized"])
    getNext = int(request.form["getNext"])
    ts = int(time.time())

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE questionId = {questionId} AND userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()

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
            cur.execute(f"SELECT * FROM MyMemorized WHERE userId = {userId} AND questionId = {questionId}")
            if len(cur.fetchall()) == 0:
                cur.execute(f"INSERT INTO MyMemorized VALUES ({userId}, {questionId})")

                cur.execute(f"SELECT bookId FROM BookData WHERE userId = {userId} AND questionId = {questionId}")
                books = cur.fetchall()
                for book in books:
                    bookId = book[0]
                    cur.execute(f"SELECT progress FROM BookProgress WHERE bookId = {bookId} AND userId = {userId}")
                    p = cur.fetchall()
                    if len(p) == 0:
                        cur.execute(f"INSERT INTO BookProgress VALUES ({userId}, {bookId}, 1)")
                    else:
                        p = p[0][0]
                        cur.execute(f"UPDATE BookProgress SET progress = {p + 1} WHERE bookId = {bookId} AND userId = {userId}")

    conn.commit()

    if getNext == 1:
        bookId = int(request.form["bookId"])

        questionId = getChallengeQuestionId(userId, bookId)

        if questionId == -1:
            return json.dumps({"questionId": questionId, "question": "Out of challenge", "answer": "You are super! No more challenge can be done!", "status": 1})

        cur.execute(f"SELECT question, answer, status FROM QuestionList WHERE questionId = {questionId} AND userId = {userId}")
        d = cur.fetchall()
        (question, answer, status) = d[0]
        question = decode(question)
        answer = decode(answer)

        mixcnt = int(request.form["mixcnt"])
        mix = []
        qs = list(getQuestionsInBook(userId, bookId, "status >= 0"))
        for _ in range(mixcnt):
            random.shuffle(qs)
        for i in range(mixcnt):
            mix.append({"question": decode(qs[i][1]), "answer": decode(qs[i][2])})

        return json.dumps({"questionId": questionId, "question": question, "answer": answer, "status": status, "mix": mix})

    else:
        return json.dumps({"success": True})