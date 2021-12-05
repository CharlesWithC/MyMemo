# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time
import json

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Book API
# Info

@app.route("/api/book", methods = ['POST'])
def apiGetBook():
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []

    questions = []
    cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId}")
    t = cur.fetchall()
    for tt in t:
        questions.append(tt[0])
    
    ret.append({"bookId": 0, "name": "All questions", "questions": questions, "anonymous": 0,
        "groupId": -1, "groupCode": "", \
            "isGroupOwner": False, "isGroupEditor": True, \
                "discoveryId": -1, "groupDiscoveryId": -1})

    cur.execute(f"SELECT bookId, name FROM Book WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        questions = getBookData(userId, dd[0])
        
        cur.execute(f"SELECT groupId FROM GroupMember WHERE userId = {userId} AND bookId = {dd[0]}")
        t = cur.fetchall()
        groupId = -1
        gcode = ""
        if len(t) != 0:
            groupId = t[0][0]
            gcode = "@pvtgroup"
            cur.execute(f"SELECT groupCode FROM GroupInfo WHERE groupId = {groupId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                gcode = "@" + tt[0][0]
        
        isGroupOwner = False
        isGroupEditor = False
        anonymous = 0
        if groupId != -1:
            owner = 0
            cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                owner = tt[0][0]
            if owner == userId:
                isGroupOwner = True
                isGroupEditor = True
            
            cur.execute(f"SELECT anonymous FROM GroupInfo WHERE groupId = {groupId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                anonymous = tt[0][0]
            
            if not isGroupOwner:
                cur.execute(f"SELECT userId FROM GroupMember WHERE groupId = {groupId} AND userId = {userId} AND isEditor = 1")
                if len(cur.fetchall()) != 0:
                    isGroupEditor = True
        
        cur.execute(f"SELECT progress FROM Book WHERE userId = {userId} AND bookId = {dd[0]}")
        t = cur.fetchall()
        progress = 0
        if len(t) > 0:
            progress = t[0][0]
        
        discoveryId = -1
        cur.execute(f"SELECT discoveryId FROM Discovery WHERE bookId = {dd[0]} AND publisherId = {userId} AND type = 1")
        t = cur.fetchall()
        if len(t) != 0:
            discoveryId = t[0][0]
        
        groupDiscoveryId = -1
        cur.execute(f"SELECT discoveryId FROM Discovery WHERE bookId = {groupId} AND bookId = {userId} AND type = 2")
        t = cur.fetchall()
        if len(t) != 0:
            groupDiscoveryId = t[0][0]

        ret.append({"bookId": dd[0], "name": decode(dd[1]), "questions": questions, "progress": progress, \
            "anonymous": anonymous, "groupId": groupId, "groupCode": gcode, \
                "isGroupOwner": isGroupOwner, "isGroupEditor": isGroupEditor, \
                "discoveryId": discoveryId, "groupDiscoveryId": groupDiscoveryId})
    
    return json.dumps(ret)

@app.route("/api/book/questionList", methods = ['POST'])
def apiGetQuestionList():
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []
    cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        ret.append({"questionId": dd[0], "question": decode(dd[1]), "answer": decode(dd[2]), "status": dd[3]})
    
    return json.dumps(ret)

@app.route("/api/book/chart", methods = ['POST'])
def apiGetBookChart():
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    bookId = int(request.form["bookId"])

    book = []
    if bookId > 0:
        book = getBookData(userId, bookId)
    else:
        cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId}")
        t = cur.fetchall()
        for tt in t:
            book.append(tt[0])
    
    d1 = []
    batch = 3
    for i in range(30):
        cur.execute(f"SELECT questionId FROM ChallengeRecord WHERE userId = {userId} AND memorized = 1 AND timestamp >= {int(time.time()/86400+1)*86400 - 86400*batch*(i+1)} AND timestamp <= {int(time.time()/86400+1)*86400 - 86400*batch*i}")
        t = cur.fetchall()
        memorized = 0
        if len(t) > 0:
            for tt in t:
                if tt[0] in book:
                    memorized += 1

        cur.execute(f"SELECT questionId FROM ChallengeRecord WHERE userId = {userId} AND memorized = 0 AND timestamp >= {int(time.time()/86400+1)*86400 - 86400*batch*(i+1)} AND timestamp <= {int(time.time()/86400+1)*86400 - 86400*batch*i}")
        t = cur.fetchall()
        forgotten = 0
        if len(t) > 0:
            for tt in t:
                if tt[0] in book:
                    forgotten += 1
        
        d1.append({"index": 30 - i, "memorized": memorized, "forgotten": forgotten})
    
    d2 = []
    total_memorized = 0
    batch = 3
    for i in range(30):
        cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId} AND memorizedTimestamp != 0 AND memorizedTimestamp <= {int(time.time()/86400+1)*86400 - 86400*batch*i}")
        t = cur.fetchall()
        total = 0
        if len(t) > 0:
            for tt in t:
                if tt[0] in book:
                    total += 1
        total_memorized = max(total_memorized, total)
        d2.append({"index": 30 - i, "total": total})
    
    cnt = len(book)

    tagcnt = 0
    cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId} AND status = 2")
    t = cur.fetchall()
    if len(t) > 0:
        for tt in t:
            if tt[0] in book:
                tagcnt += 1

    delcnt = 0
    cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId} AND status = 3")
    t = cur.fetchall()
    if len(t) > 0:
        for tt in t:
            if tt[0] in book:
                delcnt += 1

    return json.dumps({"challenge_history": d1, "total_memorized_history": d2, "tag_cnt": tagcnt, "del_cnt": delcnt, "total_memorized": total_memorized, "total": cnt})