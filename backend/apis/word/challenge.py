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





##########
# Word API
# Challenge Mode

rnd=[1,1,1,1,1,1,1,2,2,2,2,2,2,3,3,3,3,3,3,4]
def getChallengeWordId(userId, wordBookId, nofour = False):
    cur = conn.cursor()
    wordId = -1

    # just an interesting random function
    random.shuffle(rnd)
    t = rnd[random.randint(0,len(rnd)-1)]
    while t == 4 and nofour:
        random.shuffle(rnd)
        t = rnd[random.randint(0,len(rnd)-1)]
    
    cache = getWordsInWordBook(userId, wordBookId, "status = 1")
    
    if t == 1: # tagged word
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} AND userId = {userId} ORDER BY wordId ASC")
        d1 = cur.fetchall()

        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 2 AND userId = {userId} ORDER BY wordId ASC")
            d2 = cur.fetchall()
            words = []
            for dd in d2:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    words.append(wordId)

            if len(words) != 0:
                wordId = words[random.randint(0, len(words) - 1)]

        else:
            d = getWordsInWordBook(userId, wordBookId, "status = 2")
            oklist = []
            for dd in d:
                if (dd[0],) in d1:
                    oklist.append(dd[0])
            
            if len(oklist) != 0:
                wordId = oklist[random.randint(0,len(oklist)-1)]


        if wordId == -1:
            t = 2
    
    if t == 2: # words pending next challenge (already challenged)
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE nextChallenge <= {int(time.time())} AND nextChallenge != 0 AND userId = {userId} ORDER BY nextChallenge ASC")
        d1 = cur.fetchall()
        words = []
        
        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 AND userId = {userId} ORDER BY wordId ASC")
            d2 = cur.fetchall()
            for dd in d1:
                if (dd[0],) in d2:
                    wordId = dd[0]
                    words.append(wordId)
            if len(words) != 0:
                wordId = words[random.randint(0, len(words) - 1)]

        else:
            d = cache
            for dd in d:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    words.append(wordId)
        
        if len(words) != 0:
            wordId = words[random.randint(0, len(words) - 1)]
        
        if wordId == -1:
            t = 3
    
    if t == 3: # words not challenged before
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE nextChallenge = 0 AND userId = {userId} ORDER BY wordId ASC")
        d1 = cur.fetchall()
        words = []

        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 AND userId = {userId} ORDER BY wordId ASC")
            d2 = cur.fetchall()
            for dd in d1:
                if (dd[0],) in d2:
                    wordId = dd[0]
                    words.append(wordId)

        else:
            d = cache
            for dd in d:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    words.append(wordId)
        
        if len(words) != 0:
            wordId = words[random.randint(0, len(words) - 1)]
        
        if wordId == -1:
            t = 5
    
    if t == 5: # words already challenged (and not pending challenge), but last challenge is 20 minutes ago
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} AND nextChallenge != 0 AND userId = {userId} ORDER BY nextChallenge ASC")
        d1 = cur.fetchall()
        words = []
        
        if wordBookId == 0:
            cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 AND userId = {userId} ORDER BY wordId ASC")
            d2 = cur.fetchall()
            for dd in d1:
                if (dd[0],) in d2:
                    wordId = dd[0]
                    words.append(wordId)
        else:
            d = cache
            words = []
            for dd in d:
                if (dd[0],) in d1:
                    wordId = dd[0]
                    words.append(wordId)
        
        if len(words) != 0:
            wordId = words[random.randint(0, len(words) - 1)]
        
        if wordId == -1:
            t = 4
    
    if t == 4 and not nofour: # deleted word
        cur.execute(f"SELECT wordId FROM WordList WHERE status = 3 AND userId = {userId} ORDER BY RANDOM() LIMIT 1")
        d = cur.fetchall()
        if len(d) != 0:
            if wordBookId == 0:
                wordId = d[0][0]
            
            else:
                cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
                d2 = cur.fetchall()
                for dd in d2:
                    if (dd[0],) in d:
                        wordId = dd[0]
                        break
        
        if wordId == -1:
            wordId = getChallengeWordId(userId, wordBookId, nofour = True)
    
    return wordId

@app.route("/api/word/challenge/next", methods = ['POST'])
def apiGetNextChallenge():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordBookId = int(request.form["wordBookId"])
    wordId = getChallengeWordId(userId, wordBookId)

    if wordId == -1:
        return json.dumps({"wordId": wordId, "word": "Out of challenge", "translation": "You are super!\nNo more challenge can be done!", "status": 1})

    cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    (word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

# addtime = [20 minute, 1 hour, 3 hour, 8 hour, 1 day, 2 day, 5 day, 10 day]
addtime = [300, 1200, 3600, 10800, 28800, 86401, 172800, 432000, 864010]
@app.route("/api/word/challenge/update", methods = ['POST'])
def apiUpdateChallengeRecord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordId = int(request.form["wordId"])
    memorized = int(request.form["memorized"])
    getNext = int(request.form["getNext"])
    ts = int(time.time())

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE wordId = {wordId} AND userId = {userId} ORDER BY timestamp DESC")
    d = cur.fetchall()

    cur.execute(f"INSERT INTO ChallengeRecord VALUES ({userId}, {wordId}, {memorized}, {ts})")
    cur.execute(f"UPDATE ChallengeData SET lastChallenge = {ts} WHERE wordId = {wordId}  AND userId = {userId}")

    tot = 0
    if memorized == 1:
        tot = 1
        for dd in d:
            if dd[0] == 1:
                tot += 1
        if tot > 8:
            tot = 8
        cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[tot]} WHERE wordId = {wordId} AND userId = {userId}")

    elif memorized == 0:
        cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[0]} WHERE wordId = {wordId} AND userId = {userId}")
    
    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE wordId = {wordId} AND userId = {userId} ORDER BY timestamp DESC")
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
            cur.execute(f"SELECT * FROM WordMemorized WHERE userId = {userId} AND wordId = {wordId}")
            if len(cur.fetchall()) == 0:
                cur.execute(f"INSERT INTO WordMemorized VALUES ({userId}, {wordId})")

                cur.execute(f"SELECT wordBookId FROM WordBookData WHERE userId = {userId} AND wordId = {wordId}")
                wordBooks = cur.fetchall()
                for wordBook in wordBooks:
                    wordBookId = wordBook[0]
                    cur.execute(f"SELECT progress FROM WordBookProgress WHERE wordBookId = {wordBookId} AND userId = {userId}")
                    p = cur.fetchall()
                    if len(p) == 0:
                        cur.execute(f"INSERT INTO WordBookProgress VALUES ({userId}, {wordBookId}, 1)")
                    else:
                        p = p[0][0]
                        cur.execute(f"UPDATE WordBookProgress SET progress = {p + 1} WHERE wordBookId = {wordBookId} AND userId = {userId}")

    conn.commit()

    if getNext == 1:
        wordBookId = int(request.form["wordBookId"])

        wordId = getChallengeWordId(userId, wordBookId)

        if wordId == -1:
            return json.dumps({"wordId": wordId, "word": "Out of challenge", "translation": "You are super! No more challenge can be done!", "status": 1})

        cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
        d = cur.fetchall()
        (word, translation, status) = d[0]
        word = decode(word)
        translation = decode(translation)

        return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

    else:
        return json.dumps({"success": True})