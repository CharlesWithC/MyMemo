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
# Data Update (Add word / Delete word)

@app.route("/api/wordBook/addWord", methods = ['POST'])
def apiAddToWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    words = json.loads(request.form["words"])
    wordBookId = int(request.form["wordBookId"])

    cur.execute(f"SELECT name FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})
        
    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})
    
    cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()

    cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    t = cur.fetchall()

    for wordId in words:
        if (wordId,) in d and not (wordId,) in t:
            cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
            d.append((wordId,))
            t.append((wordId,))

            if groupId != -1:
                cur.execute(f"SELECT word, translation FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
                p = cur.fetchall()[0]
                word = p[0]
                translation = p[1]

                gwordId = 1
                cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 5 AND userId = {groupId}")
                d = cur.fetchall()
                if len(d) == 0:
                    cur.execute(f"INSERT INTO IDInfo VALUES (5, {groupId}, 2)")
                else:
                    gwordId = d[0][0]
                    cur.execute(f"UPDATE IDInfo SET nextId = {gwordId + 1} WHERE type = 5 AND userId = {groupId}")
                
                cur.execute(f"INSERT INTO GroupWord VALUES ({groupId}, {gwordId}, '{word}', '{translation}')")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {wordId}, {gwordId})")
                
                cur.execute(f"SELECT userId, wordBookId FROM GroupBind WHERE groupId = {groupId}")
                t = cur.fetchall()
                for tt in t:
                    uid = tt[0]
                    if uid == userId:
                        continue
                    wbid = tt[1]

                    wid = 1
                    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {uid}")
                    d = cur.fetchall()
                    if len(d) == 0:
                        cur.execute(f"INSERT INTO IDInfo VALUES (2, {uid}, 2)")
                    else:
                        wid = d[0][0]
                        cur.execute(f"UPDATE IDInfo SET nextId = {wid + 1} WHERE type = 2 AND userId = {uid}")
                   
                    cur.execute(f"INSERT INTO WordList VALUES ({uid}, {wid}, '{word}', '{translation}', 1)")
                    cur.execute(f"INSERT INTO WordBookData VALUES ({uid}, {wbid}, {wid})")
                    cur.execute(f"INSERT INTO ChallengeData VALUES ({uid},{wid},0,-1)")
                    cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {uid}, {wid}, {gwordId})")
                    updateWordStatus(uid, wid, -3) # -3 is group word
                    updateWordStatus(uid, wid, 1) # 1 is default status
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/wordBook/deleteWord", methods = ['POST'])
def apiDeleteFromWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    words = json.loads(request.form["words"])
    wordBookId = int(request.form["wordBookId"])

    cur.execute(f"SELECT name FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

    
    cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()

    for wordId in words:
        if (wordId,) in d:
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId} AND wordId = {wordId}")
            
            if groupId != -1:
                cur.execute(f"SELECT wordIdOfGroup FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
                gwordId = cur.fetchall()
                if len(gwordId) == 0:
                    continue
                gwordId = gwordId[0][0]
                cur.execute(f"DELETE FROM GroupWord WHERE groupId = {groupId} AND groupWordId = {gwordId}")
                cur.execute(f"SELECT userId, wordIdOfUser FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
                t = cur.fetchall()
                for tt in t:
                    uid = tt[0]
                    if uid == userId:
                        continue
                    wid = tt[1]
                    cur.execute(f"DELETE FROM WordList WHERE userId = {uid} AND wordId = {wid}")
                    cur.execute(f"DELETE FROM WordBookData WHERE userId = {uid} AND wordId = {wid}")
                cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
                cur.execute(f"DELETE FROM GroupWord WHERE groupWordId = {gwordId}")
    
    conn.commit()

    return json.dumps({"success": True})