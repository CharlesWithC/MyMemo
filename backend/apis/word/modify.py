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


##########
# Word API
# Modify (Add, Edit, Delete, Status Update)

duplicate = []
@app.route("/api/word/add", methods = ['POST'])
def apiAddWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["addToWordBook"])
    groupId = -1
    if wordBookId != 0:
        cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
        d = cur.fetchall()
        if len(d) != 0:
            groupId = d[0][0]
            cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
            isEditor = cur.fetchall()[0][0]
            if isEditor == 0:
                return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

    max_allow = config.max_word_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_allow != -1 and d[0][0] + 1 >= max_allow:
        return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help."})

    word = request.form["word"].replace("\\n","\n")
    word = encode(word)

    if not (userId, word) in duplicate:
        cur.execute(f"SELECT * FROM WordList WHERE word = '{word}' AND userId = {userId}")
        if len(cur.fetchall()) != 0:
            duplicate.append((userId, word))
            return json.dumps({"success": False, "msg": "Word duplicated! Add again to ignore."})
    else:
        duplicate.remove((userId, word))

    translation = request.form["translation"].replace("\\n","\n")
    translation = encode(translation)

    wordId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
    else:
        wordId = d[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {wordId + 1} WHERE type = 2 AND userId = {userId}")

    cur.execute(f"INSERT INTO WordList VALUES ({userId},{wordId},'{word}','{translation}',1)")
    cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId},0,-1)")
    updateWordStatus(userId, wordId, -2) # -2 is website added word
    updateWordStatus(userId, wordId, 1)

    if wordBookId != -1:
        cur.execute(f"SELECT wordBookId FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
        if len(cur.fetchall()) != 0:
            cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
    
    if groupId != -1:
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

    return json.dumps({"success": True, "msg": "Word added!"})

@app.route("/api/word/edit", methods = ['POST'])
def apiEditWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    wordId = int(request.form["wordId"])

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

    word = encode(request.form["word"].replace("\\n","\n"))
    translation = encode(request.form["translation"].replace("\\n","\n"))

    cur.execute(f"SELECT * FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word does not exist!"})
    
    cur.execute(f"UPDATE WordList SET word = '{word}' WHERE wordId = {wordId} AND userId = {userId}")
    cur.execute(f"UPDATE WordList SET translation = '{translation}' WHERE wordId = {wordId} AND userId = {userId}")

    if groupId != -1:
        cur.execute(f"SELECT wordIdOfGroup FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
        tt = cur.fetchall()
        if len(tt) != 0:
            gwordId = tt[0][0]
            cur.execute(f"UPDATE GroupWord SET word = '{word}' WHERE groupId = {groupId} AND groupWordId = {gwordId}")
            cur.execute(f"UPDATE GroupWord SET translation = '{translation}' WHERE groupId = {groupId} AND groupWordId = {gwordId}")
            cur.execute(f"SELECT userId, wordIdOfUser FROM GroupSync WHERE groupId = {groupId} AND wordIdOfGroup = {gwordId}")
            t = cur.fetchall()
            for tt in t:
                uid = tt[0]
                if uid == userId:
                    continue
                wid = tt[1]
                cur.execute(f"UPDATE WordList SET word = '{word}' WHERE userId = {uid} AND wordId = {wid}")
                cur.execute(f"UPDATE WordList SET translation = '{translation}' WHERE userId = {uid} AND wordId = {wid}")

    conn.commit()

    return json.dumps({"success":True})

@app.route("/api/word/delete", methods = ['POST'])
def apiDeleteWord():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    words = json.loads(request.form["words"])

    for wordId in words:
        groupId = -1
        cur.execute(f"SELECT groupId FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
        d = cur.fetchall()
        if len(d) != 0:
            groupId = d[0][0]
            cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
            isEditor = cur.fetchall()[0][0]
            if isEditor == 0:
                return json.dumps({"success": False, "msg": "You are not allowed to edit this word in group as you are not an editor! Clone the word book to edit!"})

        cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
        d = cur.fetchall()
        if len(d) > 0: # make sure word not deleted
            ts = int(time.time())
            dd = d[0]
            # cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
            cur.execute(f"DELETE FROM WordList WHERE userId = {userId} AND wordId = {wordId}")
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordId = {wordId}")
            
        if groupId != -1:
            cur.execute(f"SELECT wordIdOfGroup FROM GroupSync WHERE userId = {userId} AND wordIdOfUser = {wordId}")
            tt = cur.fetchall()
            if len(tt) == 0:
                continue # sync data lost, skip sync
            gwordId = tt[0][0] 
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

@app.route("/api/word/clearDeleted", methods = ['POST'])
def apiClearDeleted():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId} AND status = 3")
    d = cur.fetchall()
    ts = int(time.time())
    cur.execute(f"DELETE FROM WordList WHERE userId = {userId} AND status = 3")
    # for dd in d:
    #     cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
    for dd in d:
        cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordId = {dd[0]}")
    conn.commit()

    return json.dumps({"success": True})
    
@app.route("/api/word/status/update", methods = ['POST'])
def apiUpdateWordStatus():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    words = json.loads(request.form["words"])
    status = int(request.form["status"])

    if status < 1 or status > 3:
        return json.dumps({"success": False, "msg": "Invalid status code!"})

    for wordId in words:
        cur.execute(f"SELECT word FROM WordList WHERE wordId = {wordId} AND userId = {userId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"succeed": False, "msg": "Word not found!"})

        cur.execute(f"UPDATE WordList SET status = {status} WHERE wordId = {wordId} AND userId = {userId}")

        updateWordStatus(userId, wordId, status)

    conn.commit()

    return json.dumps({"succeed": True})