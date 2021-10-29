# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time
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


##########
# Word Book API
# Info

@app.route("/api/wordBook", methods = ['POST'])
def apiGetWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []

    words = []
    cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId}")
    t = cur.fetchall()
    for tt in t:
        words.append(tt[0])
    
    cur.execute(f"SELECT shareCode FROM WordBookShare WHERE wordBookId = 0 AND userId = {userId}")
    t = cur.fetchall()
    shareCode = ""
    if len(t) != 0:
        shareCode = "!"+t[0][0]
    
    ret.append({"wordBookId": 0, "name": "All words", "words": words, "shareCode": shareCode, "groupId": -1, "groupCode": "", "isGroupOwner": False})

    cur.execute(f"SELECT wordBookId, name FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        words = []
        cur.execute(f"SELECT wordId FROM WordBookData WHERE wordBookId = {dd[0]} AND userId = {userId}")
        t = cur.fetchall()
        for tt in t:
            words.append(tt[0])

        cur.execute(f"SELECT shareCode FROM WordBookShare WHERE wordBookId = {dd[0]} AND userId = {userId}")
        t = cur.fetchall()
        shareCode = ""
        if len(t) != 0:
            shareCode = "!" + t[0][0]
        
        cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {dd[0]}")
        t = cur.fetchall()
        groupId = -1
        gcode = ""
        if len(t) != 0:
            groupId = t[0][0]
            cur.execute(f"SELECT groupCode FROM GroupInfo WHERE groupId = {groupId}")
            gcode = "@" + cur.fetchall()[0][0]
        
        isGroupOwner = False
        if groupId != -1:
            cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
            owner = cur.fetchall()[0][0]
            if owner == userId:
                isGroupOwner = True
        
        cur.execute(f"SELECT progress FROM WordBookProgress WHERE userId = {userId} AND wordBookId = {dd[0]}")
        t = cur.fetchall()
        progress = 0
        if len(t) == 0:
            cur.execute(f"INSERT INTO WordBookProgress VALUES ({userId}, {dd[0]}, 0)")
            conn.commit()
        else:
            progress = t[0][0]

        ret.append({"wordBookId": dd[0], "name": decode(dd[1]), "words": words, "progress": progress, "shareCode": shareCode, "groupId": groupId, "groupCode": gcode, "isGroupOwner": isGroupOwner})
    
    return json.dumps(ret)

@app.route("/api/wordBook/wordList", methods = ['POST'])
def apiGetWordList():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []
    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        ret.append({"wordId": dd[0], "word": decode(dd[1]), "translation": decode(dd[2]), "status": dd[3]})
    
    return json.dumps(ret)