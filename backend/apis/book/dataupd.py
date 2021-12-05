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
# Data Update (Add question / Delete question)

@app.route("/api/book/addQuestion", methods = ['POST'])
def apiAddToBook():
    conn = newconn()
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
    cur.execute(f"SELECT groupId, isEditor FROM GroupMember WHERE userId = {userId} AND bookId = {bookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        isEditor = d[0][1]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this question in group as you are not an editor! Clone the book to edit!"})
    
    cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    d = list(d)

    t = getBookData(userId, bookId)

    for questionId in questions:
        if (questionId,) in d and not questionId in t:
            appendBookData(userId, bookId, questionId)
            t.append(questionId)

            if groupId != -1:
                p = None
                cur.execute(f"SELECT question, answer FROM QuestionList WHERE userId = {userId} AND questionId = {questionId}")
                tt = cur.fetchall()
                if len(tt) > 0:
                    p = tt[0]
                else:
                    continue

                question = p[0]
                answer = p[1]

                gquestionId = 1
                cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 5 AND userId = {groupId}")
                tt = cur.fetchall()
                if len(tt) == 0:
                    cur.execute(f"INSERT INTO IDInfo VALUES (5, {groupId}, 2)")
                else:
                    gquestionId = tt[0][0]
                    cur.execute(f"UPDATE IDInfo SET nextId = {gquestionId + 1} WHERE type = 5 AND userId = {groupId}")
                
                cur.execute(f"INSERT INTO GroupQuestion VALUES ({groupId}, {gquestionId}, '{question}', '{answer}')")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {questionId}, {gquestionId})")
                
                cur.execute(f"SELECT userId, bookId FROM GroupMember WHERE groupId = {groupId}")
                ttt = cur.fetchall()
                for tt in ttt:
                    uid = abs(tt[0])
                    wbid = tt[1]

                    if uid == userId:
                        continue

                    wid = 1
                    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {uid}")
                    p = cur.fetchall()
                    if len(p) == 0:
                        cur.execute(f"INSERT INTO IDInfo VALUES (2, {uid}, 2)")
                    else:
                        wid = p[0][0]
                        cur.execute(f"UPDATE IDInfo SET nextId = {wid + 1} WHERE type = 2 AND userId = {uid}")

                    cur.execute(f"SELECT questionId, answer FROM QuestionList WHERE userId = {uid} AND question = '{question}'")
                    p = cur.fetchall()
                    ctn = False
                    for pp in p:
                        if pp[1] == answer: # question completely the same
                            appendBookData(uid, wbid, pp[0])
                            cur.execute(f"SELECT memorizedTimestamp FROM QuestionList WHERE userId = {uid} AND questionId = {pp[0]}")
                            k = cur.fetchall()
                            if len(k) != 0 and k[0][0] != 0:
                                cur.execute(f"UPDATE Book SET progress = progress + 1 WHERE userId = {uid} AND bookId = {wbid}")
                            ctn = True
                            break
                    if ctn:
                        continue

                    cur.execute(f"INSERT INTO QuestionList VALUES ({uid}, {wid}, '{question}', '{answer}', 1, 0)")
                    appendBookData(uid, wbid, wid)
                    cur.execute(f"INSERT INTO ChallengeData VALUES ({uid},{wid},0,-1)")
                    cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {uid}, {wid}, {gquestionId})")
                    updateQuestionStatus(uid, wid, -3) # -3 is group question
                    updateQuestionStatus(uid, wid, 1) # 1 is default status

    conn.commit()

    return json.dumps({"success": True})

@app.route("/api/book/deleteQuestion", methods = ['POST'])
def apiDeleteFromBook():
    conn = newconn()
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
    cur.execute(f"SELECT groupId, isEditor FROM GroupMember WHERE userId = {userId} AND bookId = {bookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        isEditor = d[0][1]
        if isEditor == 0:
            return json.dumps({"success": False, "msg": "You are not allowed to edit this question in group as you are not an editor! Clone the book to edit!"})

    d = getBookData(userId, bookId)

    for questionId in questions:
        if questionId in d:
            removeBookData(userId, bookId, questionId)
            cur.execute(f"SELECT memorizedTimestamp FROM QuestionList WHERE userId = {userId} AND questionId = {questionId}")
            k = cur.fetchall()
            if len(k) > 0 and k[0][0] != 0:
                cur.execute(f"SELECT bookId FROM GroupMember WHERE userId = {userId}")
                k = cur.fetchall()
                if len(k) > 0:
                    bid = k[0][0]
                    cur.execute(f"UPDATE Book SET progress = progress - 1 WHERE userId = {userId} AND bookId = {bookId}")
            
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
                    if uid == userId or uid < 0:
                        continue
                    wid = tt[1]
                    cur.execute(f"SELECT memorizedTimestamp FROM QuestionList WHERE userId = {uid} AND questionId = {wid}")
                    k = cur.fetchall()
                    if len(k) > 0 and k[0][0] != 0:
                        cur.execute(f"SELECT bookId FROM GroupMember WHERE userId = {uid}")
                        k = cur.fetchall()
                        if len(k) > 0:
                            bid = k[0][0]
                            cur.execute(f"UPDATE Book SET progress = progress - 1 WHERE userId = {uid} AND bookId = {bid}")
                    if len(getBookId(uid, wid)) == 1: # the question is only included in the group book
                        removeBookData(uid, -1, wid)
                        cur.execute(f"DELETE FROM QuestionList WHERE userId = {uid} AND questionId = {wid}")
                    else:
                        removeBookData(uid, bid, wid)
                cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND questionIdOfGroup = {gquestionId}")
                cur.execute(f"DELETE FROM GroupQuestion WHERE groupQuestionId = {gquestionId}")
    
    conn.commit()

    return json.dumps({"success": True})