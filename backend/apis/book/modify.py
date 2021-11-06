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





def updateQuestionStatus(userId, questionId, status):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    questionUpdateId = 0
    if len(d) != 0:
        questionUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({userId},{questionId},{questionUpdateId},{status},{int(time.time())})")
    
def validateToken(userId, token):
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0 or d[0][0] == "@deleted":
        return False
    
    return sessions.validateToken(userId, token)


##########
# Book API
# Modify (Create, Clone, Delete, Rename, Share)

@app.route("/api/book/create", methods = ['POST'])
def apiCreateBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    name = str(request.form["name"])

    if name.startswith("!") and name[1:].isalnum():
        name = name[1:]
        cur.execute(f"SELECT userId, bookId FROM BookShare WHERE shareCode = '{name}'")
        d = cur.fetchall()
        if len(d) != 0:
            sharerUserId = d[0][0]
            sharerBookId = d[0][1]

            cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {sharerUserId}")
            if len(cur.fetchall()) == 0:
                return json.dumps({"success": False, "msg": "Invalid share code!"})
            
            sharerUsername = "Unknown"
            cur.execute(f"SELECT username FROM UserInfo WHERE userId = {sharerUserId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                sharerUsername = tt[0][0]
            name = encode(sharerUsername + "'s book")
            if sharerBookId != 0:
                # create book
                name = "Unknown Book"
                cur.execute(f"SELECT name FROM Book WHERE userId = {sharerUserId} AND bookId = {sharerBookId}")
                tt = cur.fetchall()
                if len(tt) > 0:
                    name = tt[0][0]

            t = []
            if sharerBookId != 0:
                cur.execute(f"SELECT questionId FROM BookData WHERE userId = {sharerUserId} AND bookId = {sharerBookId}")
                t = cur.fetchall()
            else:
                cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {sharerUserId}")
                t = cur.fetchall()
            cur.execute(f"SELECT questionId, question, answer FROM QuestionList WHERE userId = {sharerUserId}")
            b = cur.fetchall()
            di = {}
            for bb in b:
                di[bb[0]] = (bb[1], bb[2])
            
            max_allow = config.max_question_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'question_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_allow != -1 and d[0][0] + len(t) >= max_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added questions {max_allow}. Remove some old questions or contact administrator for help."})

            max_book_allow = config.max_book_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'book_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_book_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM Book WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created book {max_allow}. Remove some books (this will not remove the questions) or contact administrator for help."})

            bookId = 1
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 3 AND userId = {userId}")
            d = cur.fetchall()
            if len(d) == 0:
                cur.execute(f"INSERT INTO IDInfo VALUES (3, {userId}, 2)")
            else:
                bookId = d[0][0]
                cur.execute(f"UPDATE IDInfo SET nextId = {bookId + 1} WHERE type = 3 AND userId = {userId}")
                
            # do import
            cur.execute(f"INSERT INTO Book VALUES ({userId}, {bookId}, '{name}')")
            cur.execute(f"INSERT INTO BookProgress VALUES ({userId}, {bookId}, 0)")

            questionId = 1
            for tt in t:
                cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
                d = cur.fetchall()
                if len(d) == 0:
                    cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
                else:
                    questionId = d[0][0]
                    cur.execute(f"UPDATE IDInfo SET nextId = {questionId + 1} WHERE type = 2 AND userId = {userId}")
                
                cur.execute(f"SELECT questionId, answer FROM QuestionList WHERE userId = {userId} AND question = '{di[tt[0]][0]}'")
                p = cur.fetchall()
                ctn = False
                for pp in p:
                    if pp[1] == di[tt[0]][1]: # question completely the same
                        cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {pp[0]})")
                        cur.execute(f"SELECT * FROM MyMemorized WHERE userId = {userId} AND questionId = {pp[0]}")
                        if len(cur.fetchall()) != 0:
                            cur.execute(f"UPDATE BookProgress SET progress = progress + 1 WHERE userId = {userId} AND bookId = {bookId}")
                        ctn = True
                        break
                if ctn:
                    continue

                cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")
                cur.execute(f"INSERT INTO QuestionList VALUES ({userId}, {questionId}, '{di[tt[0]][0]}', '{di[tt[0]][1]}', 1)")
                cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{questionId}, 0, -1)")

                updateQuestionStatus(userId, questionId, -1) # -1 is imported question
                updateQuestionStatus(userId, questionId, 1) # 1 is default status

                questionId += 1
            
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

            cur.execute(f"SELECT userId FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
            if len(cur.fetchall()) != 0:
                return json.dumps({"success": False, "msg": "You have already joined this group!"})
            
            cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
            owner = 0
            t = cur.fetchall()
            if t > 0:
                owner = t[0][0]
                cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {owner}")
                if len(cur.fetchall()) == 0:
                    return json.dumps({"success": False, "msg": "Invalid group code!"})
            else:
                return json.dumps({"success": False, "msg": "Invalid group code!"})
                

            mlmt = 0
            cur.execute(f"SELECT memberLimit FROM GroupInfo WHERE groupId = {groupId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                mlmt = tt[0][0]
            cur.execute(f"SELECT * FROM GroupMember WHERE groupId = {groupId}")
            if len(cur.fetchall()) >= mlmt:
                return json.dumps({"success": False, "msg": "Group is full!"})

            cur.execute(f"SELECT question, answer, groupQuestionId FROM GroupQuestion WHERE groupId = {groupId}")
            t = cur.fetchall()
            
            # preserve limit check here as if the owner dismissed the group, the questions will remain in users' lists
            max_allow = config.max_question_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'question_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_allow != -1 and d[0][0] + len(t) >= max_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum added questions {max_allow}. Remove some old questions or contact administrator for help."})

            max_book_allow = config.max_book_per_user_allowed
            cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'book_limit'")
            pr = cur.fetchall()
            if len(pr) != 0:
                max_book_allow = pr[0][0]
            cur.execute(f"SELECT COUNT(*) FROM Book WHERE userId = {userId}")
            d = cur.fetchall()
            if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
                return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created book {max_allow}. Remove some books (this will not remove the questions) or contact administrator for help."})

            bookId = 1
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 3 AND userId = {userId}")
            d = cur.fetchall()
            if len(d) == 0:
                cur.execute(f"INSERT INTO IDInfo VALUES (3, {userId}, 2)")
            else:
                bookId = d[0][0]
                cur.execute(f"UPDATE IDInfo SET nextId = {bookId + 1} WHERE type = 3 AND userId = {userId}")

            # do import
            cur.execute(f"INSERT INTO Book VALUES ({userId}, {bookId}, '{name}')")
            cur.execute(f"INSERT INTO BookProgress VALUES ({userId}, {bookId}, 0)")
            cur.execute(f"INSERT INTO GroupMember VALUES ({groupId}, {userId}, 0)")
            cur.execute(f"INSERT INTO GroupBind VALUES ({groupId}, {userId}, {bookId})")

            questionId = 1
            for tt in t:
                cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
                d = cur.fetchall()
                if len(d) == 0:
                    cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
                else:
                    questionId = d[0][0]
                    cur.execute(f"UPDATE IDInfo SET nextId = {questionId + 1} WHERE type = 2 AND userId = {userId}")

                # no duplicate check as user are not allowed to edit questions in group
                cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")
                cur.execute(f"INSERT INTO QuestionList VALUES ({userId}, {questionId}, '{tt[0]}', '{tt[1]}', 1)")
                cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{questionId}, 0, -1)")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {questionId}, {tt[2]})")

                updateQuestionStatus(userId, questionId, -1) # -1 is imported question
                updateQuestionStatus(userId, questionId, 1) # 1 is default status

                questionId += 1
            
            conn.commit()
            return json.dumps({"success": True})
        
        else:
            return json.dumps({"success": False, "msg": "Invalid group code!"})


    name = encode(name)
    
    max_book_allow = config.max_book_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'book_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_book_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM Book WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
        return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created book {max_allow}. Remove some books (this will not remove the questions) or contact administrator for help."})

    bookId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 3 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        cur.execute(f"INSERT INTO IDInfo VALUES (3, {userId}, 2)")
    else:
        bookId = d[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {bookId + 1} WHERE type = 3 AND userId = {userId}")
    
    cur.execute(f"INSERT INTO Book VALUES ({userId}, {bookId}, '{name}')")
    cur.execute(f"INSERT INTO BookProgress VALUES ({userId}, {bookId}, 0)")
    conn.commit()
    
    return json.dumps({"success": True})

@app.route("/api/book/clone", methods = ['POST'])
def apiCloneBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cloneFrom = int(request.form["fromBook"])

    cur.execute(f"SELECT name FROM Book WHERE bookId = {cloneFrom} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Book to clone from not found!"})
    name = encode(decode(d[0][0]) + " (Clone)")
    
    max_book_allow = config.max_book_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'book_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_book_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM Book WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
        return json.dumps({"success": False, "msg": f"You have reached your limit of maximum created book {max_allow}. Remove some books (this will not remove the questions) or contact administrator for help."})

    bookId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 3 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        cur.execute(f"INSERT INTO IDInfo VALUES (3, {userId}, 2)")
    else:
        bookId = d[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {bookId + 1} WHERE type = 3 AND userId = {userId}")
    
    cur.execute(f"INSERT INTO Book VALUES ({userId}, {bookId}, '{name}')")
    cur.execute(f"SELECT questionId FROM BookData WHERE userId = {userId} AND bookId = {cloneFrom}")
    d = cur.fetchall()
    for dd in d:
        cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {dd[0]})")
    cur.execute(f"SELECT progress FROM BookProgress WHERE userId = {userId} AND bookId = {cloneFrom}")
    t = cur.fetchall()
    progress = 0
    if len(t) == 0:
        cur.execute(f"INSERT INTO BookProgress VALUES ({userId}, {cloneFrom}, 0)")
        conn.commit()
    else:
        progress = t[0][0]
    cur.execute(f"INSERT INTO BookProgress VALUES ({userId}, {bookId}, {progress})")
    
    conn.commit()
    return json.dumps({"success": True, "msg": "Book cloned!"})
    

@app.route("/api/book/delete", methods = ['POST'])
def apiDeleteBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    bookId = int(request.form["bookId"])
    cur.execute(f"SELECT name FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Book does not exist!"})

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND bookId = {bookId}")
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
            return json.dumps({"success": False, "msg": "You are the owner of the group. You have to transfer group ownership before deleting the book."})

        cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId} AND userId = {userId}")
        

    cur.execute(f"DELETE FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    cur.execute(f"DELETE FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    cur.execute(f"DELETE FROM BookProgress WHERE userId = {userId} AND bookId = {bookId}")
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/book/rename", methods = ['POST'])
def apiRenameBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    bookId = int(request.form["bookId"])
    newName = str(request.form["name"])

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE bookId = {bookId} AND userId = {userId}")
    t = cur.fetchall()
    if len(t) != 0:
        groupId = t[0][0]
        gname = "Unknown Book"
        cur.execute(f"SELECT name FROM GroupInfo WHERE groupId = {groupId}")
        tt = cur.fetchall()
        if len(tt) > 0:
            gname = tt[0][0]
        cur.execute(f"UPDATE Book SET name = '{gname}' WHERE userId = {userId} AND bookId = {bookId}")
        conn.commit()
        return json.dumps({"success": False, "msg": "You are not allowed to rename a book that is bound to a group!"})

    cur.execute(f"SELECT * FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Book does not exist!"})

    cur.execute(f"UPDATE Book SET name = '{encode(newName)}' WHERE userId = {userId} AND bookId = {bookId}")
    conn.commit()
    return json.dumps({"success": True})

@app.route("/api/book/share", methods = ['POST'])
def apiShareBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    bookId = int(request.form["bookId"])
    op = request.form["operation"]

    if op == "share":
        cur.execute(f"SELECT * FROM BookShare WHERE userId = {userId} AND bookId = {bookId}")
        if len(cur.fetchall()) != 0:
            return json.dumps({"success": False, "msg": "Book already shared!"})
        else:
            shareCode = genCode(8)
            cur.execute(f"SELECT * FROM BookShare WHERE shareCode = '{shareCode}'")
            if len(cur.fetchall()) != 0: # conflict
                for _ in range(10):
                    shareCode = genCode(8)
                    cur.execute(f"SELECT * FROM BookShare WHERE shareCode = '{shareCode}'")
                    if len(cur.fetchall()) == 0:
                        break
                cur.execute(f"SELECT * FROM BookShare WHERE shareCode = '{shareCode}'")
                if len(cur.fetchall()) != 0:
                    return json.dumps({"success": False, "msg": "Unable to generate an unique share code..."})
                    
            cur.execute(f"INSERT INTO BookShare VALUES ({userId}, {bookId}, '{shareCode}')")
            conn.commit()
            return json.dumps({"success": True, "msg": f"Done! Share code: !{shareCode}. Tell your friend to enter it in the textbox of 'Create Book' and he / she will be able to import it!", "shareCode": f"!{shareCode}"})
    
    elif op == "unshare":
        cur.execute(f"SELECT * FROM BookShare WHERE userId = {userId} AND bookId = {bookId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"success": False, "msg": "Book not shared!"})
        else:
            cur.execute(f"DELETE FROM BookShare WHERE userId = {userId} AND bookId = {bookId}")
            conn.commit()
            return json.dumps({"success": True, "msg": "Book unshared!"})