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





def getWordCount(userId):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
    return cur.fetchall()[0][0]

def validateToken(userId, token):
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0 or d[0][0] == "@deleted":
        return False
    
    return sessions.validateToken(userId, token)


##########
# Word API
# Info

@app.route("/api/word", methods = ['POST'])
def apiGetWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordId = int(request.form["wordId"])
    
    cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()

    if len(d) == 0:
        abort(404)
    
    (word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    return json.dumps({"wordId": wordId, "word":word, "translation": translation, "status": status})

@app.route("/api/word/id", methods = ['POST'])
def apiGetWordID():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    word = request.form["word"].replace("\n","\\n")
    wordBookId = int(request.form["wordBookId"])
    cur.execute(f"SELECT wordId FROM WordList WHERE word = '{encode(word)}' AND userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0:
        wordId = d[0][0]
        if wordBookId > 0:
            cur.execute(f"SELECT wordBookId FROM WordBookData WHERE wordId = {wordId} AND wordBookId = {wordBookId}")
            if len(cur.fetchall()) == 0:
                abort(404)

        # If there are multiple records, then return the first one
        # NOTE: The user should be warned when they try to insert multiple records with the same word
        return json.dumps({"wordId" : wordId})
    else:
        abort(404)

@app.route("/api/word/stat", methods = ['POST'])
def apiGetWordStat():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordId = int(request.form["wordId"])
    cur.execute(f"SELECT word FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        abort(404)
    word = decode(d[0][0])
    
    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE wordId = {wordId} AND updateTo <= 0 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        abort(404)
    d = d[0]
    astatus = d[0] # how it is added
    ats = d[1] # addition timestamp

    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE wordId = {wordId} AND userId = {userId}")
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

    for i in range(2, len(d)):
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
        status = d[i][0]
    
    cur.execute(f"SELECT nextChallenge, lastChallenge FROM ChallengeData WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        abort(404)
    d = d[0]
    nxt = d[0]
    lst = d[1]

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE wordId = {wordId} AND userId = {userId}")
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
        return datetime.datetime.fromtimestamp(ts)

    res = f"About {word}\n"

    if astatus == 0:
        res += f"Added by magic (unknown adding method).\n"
    elif astatus == -1:
        res += f"Imported from file.\n"  
    elif astatus == -2:
        res += f"Added at {ts2dt(ats)} on website.\n"  
    elif astatus == -3:
        res += f"Imported from a group's word book."

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
    
    return json.dumps({"msg":res})

@app.route("/api/word/count", methods = ['POST'])
def apiGetWordCount():
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    return json.dumps({"count": str(getWordCount(userId))})