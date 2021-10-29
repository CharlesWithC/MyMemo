# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, datetime, time
import random
import json
import sqlite3

from app import app, config
from functions import *
import sessions


conn = sqlite3.connect("database.db", check_same_thread = False)

    
def updateWordStatus(userId, wordId, status):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    wordUpdateId = 0
    if len(d) != 0:
        wordUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({userId},{wordId},{wordUpdateId},{status},{int(time.time())})")

def validateToken(userId, token):
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0 or d[0][0] == "@deleted":
        return False
    
    return sessions.validateToken(userId, token)

def getWordsInWordBook(userId, wordBookId, statusRequirement):
    cur = conn.cursor()
    cur.execute(f"SELECT wordId FROM WordBookData WHERE wordBookId = {wordBookId} AND userId = {userId}")
    wordbook = cur.fetchall()
    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE ({statusRequirement}) AND userId = {userId}")
    words = cur.fetchall()
    d = []
    for word in words:
        if (word[0],) in wordbook:
            d.append(word)
    return d


##########
# Word API
# Practice Mode

@app.route("/api/word/next", methods = ['POST'])
def apiGetNext():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordId = -1

    op = {-1: "<", 1: ">"}
    order = {-1: "DESC", 1: "ASC"}
    moveType = int(request.form["moveType"]) # -1: previous, 1: next, 0: random
    if moveType in [-1,1]:
        op = op[moveType]
        order = order[moveType]

    current = -1
    if moveType in [-1, 1]:
        current = int(request.form["wordId"])

    statusRequirement = {1: "status = 1 OR status = 2", 2: "status = 2", 3: "status = 3"}
    status = int(request.form["status"])
    statusRequirement = statusRequirement[status]

    wordBookId = int(request.form["wordBookId"])
    
    if wordBookId == 0:
        if moveType in [-1,1]:
            cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE wordId{op}{current} AND ({statusRequirement}) AND userId = {userId} ORDER BY wordId {order} LIMIT 1")
            d = cur.fetchall()
            if len(d) == 0: # no matching results, then find result from first / end
                cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE ({statusRequirement}) AND userId = {userId} ORDER BY wordId {order} LIMIT 1")
                d = cur.fetchall()

        elif moveType == 0:
            cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE ({statusRequirement}) AND userId = {userId} ORDER BY RANDOM() LIMIT 1")
            d = cur.fetchall()
    
    else:
        d = getWordsInWordBook(userId, wordBookId, statusRequirement)
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
        return json.dumps({"wordId": -1, "word": "[No more word]", "translation": "Maybe change the settings?\nOr check your connection?", "status": 1})

    (wordId, word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})