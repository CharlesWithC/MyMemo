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
# Modify (Create, Clone, Delete, Rename, Share)

@app.route("/api/wordBook/create", methods = ['POST'])
def apiCreateWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    name = str(request.form["name"])

    wordBookId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 3 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        cur.execute(f"INSERT INTO IDInfo VALUES (3, {userId}, 2)")
    else:
        wordBookId = d[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {wordBookId + 1} WHERE type = 3 AND userId = {userId}")

    if name.startswith("!") and name[1:].isalnum():
        name = name[1:]
        cur.execute(f"SELECT userId, wordBookId FROM WordBookShare WHERE shareCode = '{name}'")
        d = cur.fetchall()
        if len(d) != 0:
            sharerUserId = d[0][0]
            sharerWordBookId = d[0][1]
            
            cur.execute(f"SELECT username FROM UserInfo WHERE userId = {sharerUserId}")
            sharerUsername = cur.fetchall()[0][0]
            name = encode(sharerUsername + "'s word book")
            if sharerWordBookId != 0:
                # create word book
                cur.execute(f"SELECT name FROM WordBook WHERE userId = {sharerUserId} AND wordBookId = {sharerWordBookId}")
                name = cur.fetchall()[0][0]

            t = []
            if sharerWordBookId != 0:
                cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {sharerUserId} AND wordBookId = {sharerWordBookId}")
                t = cur.fetchall()
            else:
                cur.execute(f"SELECT wordId FROM WordList WHERE userId = {sharerUserId}")
                t = cur.fetchall()
            cur.execute(f"SELECT wordId, word, translation FROM WordList WHERE userId = {sharerUserId}")
            b = cur.fetchall()
            di = {}
            for bb in b:
                di[bb[0]] = (bb[1], bb[2])
            
            max_allow = config.max_word_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_allow != -1 and d[0][0] + len(t) >= max_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help."})

            max_book_allow = config.max_word_book_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_book_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_book_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordBook WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created word book {max_allow}. Remove some word books (this will not remove the words) or contact administrator for help."})

            # do import
            cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")
            cur.execute(f"INSERT INTO WordBookProgress VALUES ({userId}, {wordBookId}, 0)")

            wordId = 1
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
            d = cur.fetchall()
            if len(d) == 0:
                cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
            else:
                wordId = d[0][0]
                cur.execute(f"UPDATE IDInfo SET nextId = {wordId + 1} WHERE type = 2 AND userId = {userId}")

            for tt in t:
                cur.execute(f"SELECT wordId, translation FROM WordList WHERE userId = {userId} AND word = '{di[tt[0]][0]}'")
                p = cur.fetchall()
                ctn = False
                for pp in p:
                    if pp[1] == di[tt[0]][1]: # word completely the same
                        cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {pp[0]})")
                        cur.execute(f"SELECT * FROM WordMemorized WHERE userId = {userId} AND wordId = {pp[0]}")
                        if len(cur.fetchall()) != 0:
                            cur.execute(f"UPDATE WordBookProgress SET progress = progress + 1 WHERE userId = {userId} AND wordBookId = {wordBookId}")
                        ctn = True
                        break
                if ctn:
                    continue

                cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
                cur.execute(f"INSERT INTO WordList VALUES ({userId}, {wordId}, '{di[tt[0]][0]}', '{di[tt[0]][1]}', 1)")
                cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId}, 0, -1)")

                updateWordStatus(userId, wordId, -1) # -1 is imported word
                updateWordStatus(userId, wordId, 1) # 1 is default status

                wordId += 1
            
            conn.commit()
            return json.dumps({"success": True})
        
        else:
            return json.dumps({"success": False, "msg": "Invalid share code!"})
    
    elif name.startswith("@") and name[1:].isalnum():
        if name == "@pvtgroup":
            return json.dumps({"success": False, "msg": "This is the general code of all private code and it cannot be used!"})
        name = name[1:]
        cur.execute(f"SELECT groupId, name FROM GroupInfo WHERE groupCode = '{name}'")
        d = cur.fetchall()
        if len(d) != 0:
            groupId = d[0][0]
            name = d[0][1]

            cur.execute(f"SELECT memberLimit FROM GroupInfo WHERE groupId = {groupId}")
            mlmt = cur.fetchall()[0][0]
            cur.execute(f"SELECT * FROM GroupMember WHERE groupId = {groupId}")
            if len(cur.fetchall()) >= mlmt:
                return json.dumps({"success": False, "msg": "Group is full!"})

            cur.execute(f"SELECT word, translation, groupWordId FROM GroupWord WHERE groupId = {groupId}")
            t = cur.fetchall()
            
            # preserve limit check here as if the owner dismissed the group, the words will remain in users' lists
            max_allow = config.max_word_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_allow != -1 and d[0][0] + len(t) >= max_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help."})

            max_book_allow = config.max_word_book_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_book_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_book_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM WordBook WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created word book {max_allow}. Remove some word books (this will not remove the words) or contact administrator for help."})


            # do import
            cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")
            cur.execute(f"INSERT INTO WordBookProgress VALUES ({userId}, {wordBookId}, 0)")
            cur.execute(f"INSERT INTO GroupMember VALUES ({groupId}, {userId}, 0)")
            cur.execute(f"INSERT INTO GroupBind VALUES ({groupId}, {userId}, {wordBookId})")

            wordId = 1
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
            d = cur.fetchall()
            if len(d) == 0:
                cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
            else:
                wordId = d[0][0]
                cur.execute(f"UPDATE IDInfo SET nextId = {wordId + 1} WHERE type = 2 AND userId = {userId}")
            
            for tt in t:
                # no duplicate check as user are not allowed to edit words in group
                cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
                cur.execute(f"INSERT INTO WordList VALUES ({userId}, {wordId}, '{tt[0]}', '{tt[1]}', 1)")
                cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId}, 0, -1)")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {wordId}, {tt[2]})")

                updateWordStatus(userId, wordId, -1) # -1 is imported word
                updateWordStatus(userId, wordId, 1) # 1 is default status

                wordId += 1
            
            conn.commit()
            return json.dumps({"success": True})
        
        else:
            return json.dumps({"success": False, "msg": "Invalid group code!"})


    name = encode(name)
    
    max_book_allow = config.max_word_book_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_book_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_book_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
        return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created word book {max_allow}. Remove some word books (this will not remove the words) or contact administrator for help."})

    cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")
    cur.execute(f"INSERT INTO WordBookProgress VALUES ({userId}, {wordBookId}, 0)")
    conn.commit()
    
    return json.dumps({"success": True})

@app.route("/api/wordBook/clone", methods = ['POST'])
def apiCloneWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cloneFrom = int(request.form["fromWordBook"])

    cur.execute(f"SELECT name FROM WordBook WHERE wordBookId = {cloneFrom} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Word book to clone from not found!"})
    name = encode("(Clone) " + decode(d[0][0]))
    
    max_book_allow = config.max_word_book_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_book_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_book_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM WordBook WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
        return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created word book {max_allow}. Remove some word books (this will not remove the words) or contact administrator for help."})

    wordBookId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 3 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        cur.execute(f"INSERT INTO IDInfo VALUES (3, {userId}, 2)")
    else:
        wordBookId = d[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {wordBookId + 1} WHERE type = 3 AND userId = {userId}")
    
    cur.execute(f"INSERT INTO WordBook VALUES ({userId}, {wordBookId}, '{name}')")
    cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {cloneFrom}")
    d = cur.fetchall()
    for dd in d:
        cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {dd[0]})")
    cur.execute(f"SELECT progress FROM WordBookProgress WHERE userId = {userId} AND wordBookId = {cloneFrom}")
    t = cur.fetchall()
    progress = 0
    if len(t) == 0:
        cur.execute(f"INSERT INTO WordBookProgress VALUES ({userId}, {cloneFrom}, 0)")
        conn.commit()
    else:
        progress = t[0][0]
    cur.execute(f"INSERT INTO WordBookProgress VALUES ({userId}, {wordBookId}, {progress})")
    
    conn.commit()
    return json.dumps({"success": True, "msg": "Word book cloned!"})
    

@app.route("/api/wordBook/delete", methods = ['POST'])
def apiDeleteWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["wordBookId"])
    cur.execute(f"SELECT name FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND wordBookId = {wordBookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]

    if groupId != -1:
        cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
        d = cur.fetchall()
        if len(d) == 0:
            return json.dumps({"success": False, "msg": "Group does not exist!"})
        owner = d[0][0]
        if userId == owner:
            return json.dumps({"success": False, "msg": "You are the owner of the group. You have to transfer group ownership before deleting the word book."})

        cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId} AND userId = {userId}")
        

    cur.execute(f"DELETE FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
    cur.execute(f"DELETE FROM WordBookProgress WHERE userId = {userId} AND wordBookId = {wordBookId}")
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/wordBook/rename", methods = ['POST'])
def apiRenameWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["wordBookId"])
    newName = str(request.form["name"])

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE wordBookId = {wordBookId} AND userId = {userId}")
    t = cur.fetchall()
    if len(t) != 0:
        groupId = t[0][0]
        cur.execute(f"SELECT name FROM GroupInfo WHERE groupId = {groupId}")
        gname = cur.fetchall()[0][0]
        cur.execute(f"UPDATE WordBook SET name = '{gname}' WHERE userId = {userId} AND wordBookId = {wordBookId}")
        conn.commit()
        return json.dumps({"success": False, "msg": "You are not allowed to rename a word book that is bound to a group!"})

    cur.execute(f"SELECT * FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Word book does not exist!"})

    cur.execute(f"UPDATE WordBook SET name = '{encode(newName)}' WHERE userId = {userId} AND wordBookId = {wordBookId}")
    conn.commit()
    return json.dumps({"success": True})

@app.route("/api/wordBook/share", methods = ['POST'])
def apiShareWordBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    wordBookId = int(request.form["wordBookId"])
    op = request.form["operation"]

    if op == "share":
        cur.execute(f"SELECT * FROM WordBookShare WHERE userId = {userId} AND wordBookId = {wordBookId}")
        if len(cur.fetchall()) != 0:
            return json.dumps({"success": False, "msg": "Word book already shared!"})
        else:
            shareCode = genCode(8)
            cur.execute(f"SELECT * FROM WordBookShare WHERE shareCode = '{shareCode}'")
            if len(cur.fetchall()) != 0: # conflict
                for _ in range(10):
                    shareCode = genCode(8)
                    cur.execute(f"SELECT * FROM WordBookShare WHERE shareCode = '{shareCode}'")
                    if len(cur.fetchall()) == 0:
                        break
                cur.execute(f"SELECT * FROM WordBookShare WHERE shareCode = '{shareCode}'")
                if len(cur.fetchall()) != 0:
                    return json.dumps({"success": False, "msg": "Unable to generate an unique share code..."})
                    
            cur.execute(f"INSERT INTO WordBookShare VALUES ({userId}, {wordBookId}, '{shareCode}')")
            conn.commit()
            return json.dumps({"success": True, "msg": f"Done! Share code: !{shareCode}. Tell your friend to enter it in the textbox of 'Create Word Book' and he / she will be able to import it!", "shareCode": f"!{shareCode}"})
    
    elif op == "unshare":
        cur.execute(f"SELECT * FROM WordBookShare WHERE userId = {userId} AND wordBookId = {wordBookId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"success": False, "msg": "Word book not shared!"})
        else:
            cur.execute(f"DELETE FROM WordBookShare WHERE userId = {userId} AND wordBookId = {wordBookId}")
            conn.commit()
            return json.dumps({"success": True, "msg": "Word book unshared!"})