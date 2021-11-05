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
# Data Update (Add question / Delete question)

@app.route("/api/book/addQuestion", methods = ['POST'])
def apiAddToBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    questions = json.loads(request.form["questions"])
    bookId = int(request.form["bookId"])

    cur.execute(f"SELECT name FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Book does not exist!"})
        
    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND bookId = {bookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this question in group as you are not an editor! Clone the book to edit!"})
    
    cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()

    cur.execute(f"SELECT questionId FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    t = cur.fetchall()

    for questionId in questions:
        if (questionId,) in d and not (questionId,) in t:
            cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")
            d.append((questionId,))
            t.append((questionId,))

            if groupId != -1:
                cur.execute(f"SELECT question, answer FROM QuestionList WHERE userId = {userId} AND questionId = {questionId}")
                p = cur.fetchall()[0]
                question = p[0]
                answer = p[1]

                gquestionId = 1
                cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 5 AND userId = {groupId}")
                d = cur.fetchall()
                if len(d) == 0:
                    cur.execute(f"INSERT INTO IDInfo VALUES (5, {groupId}, 2)")
                else:
                    gquestionId = d[0][0]
                    cur.execute(f"UPDATE IDInfo SET nextId = {gquestionId + 1} WHERE type = 5 AND userId = {groupId}")
                
                cur.execute(f"INSERT INTO GroupQuestion VALUES ({groupId}, {gquestionId}, '{question}', '{answer}')")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {questionId}, {gquestionId})")
                
                cur.execute(f"SELECT userId, bookId FROM GroupBind WHERE groupId = {groupId}")
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
                   
                    cur.execute(f"INSERT INTO QuestionList VALUES ({uid}, {wid}, '{question}', '{answer}', 1)")
                    cur.execute(f"INSERT INTO BookData VALUES ({uid}, {wbid}, {wid})")
                    cur.execute(f"INSERT INTO ChallengeData VALUES ({uid},{wid},0,-1)")
                    cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {uid}, {wid}, {gquestionId})")
                    updateQuestionStatus(uid, wid, -3) # -3 is group question
                    updateQuestionStatus(uid, wid, 1) # 1 is default status
    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/book/deleteQuestion", methods = ['POST'])
def apiDeleteFromBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    questions = json.loads(request.form["questions"])
    bookId = int(request.form["bookId"])

    cur.execute(f"SELECT name FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Book does not exist!"})

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND bookId = {bookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        isEditor = cur.fetchall()[0][0]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this question in group as you are not an editor! Clone the book to edit!"})

    
    cur.execute(f"SELECT questionId FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    d = cur.fetchall()

    for questionId in questions:
        if (questionId,) in d:
            cur.execute(f"DELETE FROM BookData WHERE userId = {userId} AND bookId = {bookId} AND questionId = {questionId}")
            
            if groupId != -1:
                cur.execute(f"SELECT questionIdOfGroup FROM GroupSync WHERE userId = {userId} AND questionIdOfUser = {questionId}")
                gquestionId = cur.fetchall()
                if len(gquestionId) == 0:
                    continue
                gquestionId = gquestionId[0][0]
                cur.execute(f"DELETE FROM GroupQuestion WHERE groupId = {groupId} AND groupQuestionId = {gquestionId}")
                cur.execute(f"SELECT userId, questionIdOfUser FROM GroupSync WHERE groupId = {groupId} AND questionIdOfGroup = {gquestionId}")
                t = cur.fetchall()
                for tt in t:
                    uid = tt[0]
                    if uid == userId:
                        continue
                    wid = tt[1]
                    cur.execute(f"DELETE FROM QuestionList WHERE userId = {uid} AND questionId = {wid}")
                    cur.execute(f"DELETE FROM BookData WHERE userId = {uid} AND questionId = {wid}")
                cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND questionIdOfGroup = {gquestionId}")
                cur.execute(f"DELETE FROM GroupQuestion WHERE groupQuestionId = {gquestionId}")
    
    conn.commit()

    return json.dumps({"success": True})