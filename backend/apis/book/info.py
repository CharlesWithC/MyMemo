# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time
import json

from app import app, config
import db
from functions import *
import sessions

import MySQLdb
import sqlite3
conn = None
if config.database == "mysql":
    conn = MySQLdb.connect(host = app.config["MYSQL_HOST"], user = app.config["MYSQL_USER"], \
        passwd = app.config["MYSQL_PASSWORD"], db = app.config["MYSQL_DB"])
elif config.database == "sqlite":
    conn = sqlite3.connect("database.db", check_same_thread = False)

##########
# Book API
# Info

@app.route("/api/book", methods = ['POST'])
def apiGetBook():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []

    questions = []
    cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId}")
    t = cur.fetchall()
    for tt in t:
        questions.append(tt[0])
    
    cur.execute(f"SELECT shareCode FROM BookShare WHERE bookId = 0 AND userId = {userId}")
    t = cur.fetchall()
    shareCode = ""
    if len(t) != 0:
        shareCode = "!"+t[0][0]
    
    ret.append({"bookId": 0, "name": "All questions", "questions": questions, "shareCode": shareCode, "anonymous": 0,
        "groupId": -1, "groupCode": "", \
            "isGroupOwner": False, "isGroupEditor": True, \
                "discoveryId": -1, "groupDiscoveryId": -1})

    cur.execute(f"SELECT bookId, name FROM Book WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        questions = []
        cur.execute(f"SELECT questionId FROM BookData WHERE bookId = {dd[0]} AND userId = {userId}")
        t = cur.fetchall()
        for tt in t:
            questions.append(tt[0])

        cur.execute(f"SELECT shareCode FROM BookShare WHERE bookId = {dd[0]} AND userId = {userId}")
        t = cur.fetchall()
        shareCode = ""
        if len(t) != 0:
            shareCode = "!" + t[0][0]
        
        cur.execute(f"SELECT groupId FROM GroupBind WHERE userId = {userId} AND bookId = {dd[0]}")
        t = cur.fetchall()
        groupId = -1
        gcode = ""
        if len(t) != 0:
            groupId = t[0][0]
            gcode = "@pvtgroup"
            cur.execute(f"SELECT groupCode FROM GroupInfo WHERE groupId = {groupId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                gcode = "@" + tt[0][0]
        
        isGroupOwner = False
        isGroupEditor = False
        anonymous = 0
        if groupId != -1:
            owner = 0
            cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                owner = tt[0][0]
            if owner == userId:
                isGroupOwner = True
                isGroupEditor = True
            
            cur.execute(f"SELECT anonymous FROM GroupInfo WHERE groupId = {groupId}")
            tt = cur.fetchall()
            if len(tt) > 0:
                anonymous = tt[0][0]
            
            if not isGroupOwner:
                cur.execute(f"SELECT userId FROM GroupMember WHERE groupId = {groupId} AND userId = {userId} AND isEditor = 1")
                if len(cur.fetchall()) != 0:
                    isGroupEditor = True
        
        cur.execute(f"SELECT progress FROM BookProgress WHERE userId = {userId} AND bookId = {dd[0]}")
        t = cur.fetchall()
        progress = 0
        if len(t) == 0:
            cur.execute(f"INSERT INTO BookProgress VALUES ({userId}, {dd[0]}, 0)")
            conn.commit()
        else:
            progress = t[0][0]
        
        discoveryId = -1
        cur.execute(f"SELECT discoveryId FROM Discovery WHERE bookId = {dd[0]} AND publisherId = {userId} AND type = 1")
        t = cur.fetchall()
        if len(t) != 0:
            discoveryId = t[0][0]
        
        groupDiscoveryId = -1
        cur.execute(f"SELECT discoveryId FROM Discovery WHERE bookId = {groupId} AND bookId = {userId} AND type = 2")
        t = cur.fetchall()
        if len(t) != 0:
            groupDiscoveryId = t[0][0]

        ret.append({"bookId": dd[0], "name": decode(dd[1]), "questions": questions, "progress": progress, "shareCode": shareCode, \
            "anonymous": anonymous, "groupId": groupId, "groupCode": gcode, \
                "isGroupOwner": isGroupOwner, "isGroupEditor": isGroupEditor, \
                "discoveryId": discoveryId, "groupDiscoveryId": groupDiscoveryId})
    
    return json.dumps(ret)

@app.route("/api/book/questionList", methods = ['POST'])
def apiGetQuestionList():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    ret = []
    cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    for dd in d:
        ret.append({"questionId": dd[0], "question": decode(dd[1]), "answer": decode(dd[2]), "status": dd[3]})
    
    return json.dumps(ret)