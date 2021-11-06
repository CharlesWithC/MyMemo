# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time, math
import json
import validators
import sqlite3

from app import app, config
from functions import *
import sessions
import tempdb

##########
# Discovery API

@app.route("/api/discovery/book", methods = ['GET','POST'])
def apiDiscoveryBook():
    cur = conn.cursor()
    cur.execute(f"SELECT discoveryId, title, description, publisherId FROM BookDiscovery")
    d = cur.fetchall()
    dis = []
    for dd in d:
        publisher = "Unknown User"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) != 0:
            publisher = t[0][0]
            if publisher == "@deleted":
                publisher = "Deleted Account"

        # update views
        cur.execute(f"SELECT count FROM BookDiscoveryClick WHERE discoveryId = {dd[0]}")
        views = 0
        t = cur.fetchall()
        if len(t) > 0:
            views = t[0][0]
        
        # get views and likes
        cur.execute(f"SELECT COUNT(like) FROM BookDiscoveryLike WHERE discoveryId = {dd[0]}")
        likes = 0
        t = cur.fetchall()
        if len(t) > 0:
            likes = t[0][0]

        dis.append({"discoveryId": dd[0], "title": decode(dd[1]), "description": decode(dd[2]), "publisher": publisher, "views": views, "likes": likes})
    return json.dumps(dis)

@app.route("/api/discovery/book/<int:discoveryId>", methods = ['GET', 'POST'])
def apiDiscoveryBookData(discoveryId):
    cur = conn.cursor()

    userId = 0

    if request.method == "POST":
        loggedin = False
        if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
            loggedin = False
        else:
            loggedin = True
        
        if loggedin:
            loggedin = False
            userId = int(request.form["userId"])
            token = request.form["token"]
            if validateToken(userId, token):
                loggedin = True
        
        if not loggedin:
            userId = 0
    
    cur.execute(f"SELECT publisherId, bookId, title, description FROM BookDiscovery WHERE discoveryId = {discoveryId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Book not found!"})
    d = d[0]

    uid = d[0]
    bookId = d[1]
    title = decode(d[2])
    description = decode(d[3])
    
    # Check share existence
    cur.execute(f"SELECT * FROM Book WHERE userId = {uid} AND bookId = {bookId}")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"DELETE FROM BookDiscovery WHERE discoveryId = {discoveryId}")
        conn.commit()
        return json.dumps({"success": False, "msg": "Book not found!"})
    
    # Check share status as books must be shared before being imported
    # Do not clear discovery status as publisher may just want to close it temporarily
    cur.execute(f"SELECT shareCode FROM BookShare WHERE userId = {uid} AND bookId = {bookId}")
    t = cur.fetchall()
    shareCode = ""
    if len(t) != 0:
        shareCode = "!"+t[0][0]
    
    if shareCode == "":
        return json.dumps({"success": False, "msg": "Book not shared! Maybe the publisher just closed it temporarily."})

    # Get discovery publisher username
    publisher = "Unknown User"
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) != 0:
        publisher = t[0][0]
        if publisher == "@deleted":
            publisher = "Deleted Account"
    
    isPublisher = False
    if uid == userId:
        isPublisher = True
    
    # get questions
    questions = []
    cur.execute(f"SELECT questionId FROM BookData WHERE userId = {uid} AND bookId = {bookId}")
    p = cur.fetchall()
    for pp in p:
        cur.execute(f"SELECT question, answer FROM QuestionList WHERE userId = {uid} AND questionId = {pp[0]}")
        t = cur.fetchall()
        if len(t) == 0:
            continue
        questions.append({"question": decode(t[0][0]), "answer": decode(t[0][1])})

    # update views
    cur.execute(f"SELECT count FROM BookDiscoveryClick WHERE discoveryId = {discoveryId}")
    views = 1
    t = cur.fetchall()
    if len(t) > 0:
        views = t[0][0] + 1
        cur.execute(f"UPDATE BookDiscoveryClick SET count = count + 1 WHERE discoveryId = {discoveryId}")
    else:
        cur.execute(f"INSERT INTO BookDiscoveryClick VALUES ({discoveryId}, 1)")
    conn.commit()
    
    # get views and likes
    cur.execute(f"SELECT COUNT(like) FROM BookDiscoveryLike WHERE discoveryId = {discoveryId}")
    likes = 0
    t = cur.fetchall()
    if len(t) > 0:
        likes = t[0][0]
    
    # get user liked
    cur.execute(f"SELECT like FROM BookDiscoveryLike WHERE discoveryId = {discoveryId} AND userId = {userId}")
    liked = False
    t = cur.fetchall()
    if len(t) > 0:
        liked = True
    
    return json.dumps({"title": title, "description": description, "questions": questions, "publisher": publisher, "shareCode": shareCode, "isPublisher": isPublisher, "views": views, "likes": likes, "liked": liked})

@app.route("/api/discovery/book/publish", methods = ['POST'])
def apiDiscoveryBookPublish():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    bookId = int(request.form["bookId"])
    title = encode(request.form["title"])
    description = encode(request.form["description"])

    cur.execute(f"SELECT * FROM BookDiscovery WHERE publisherId = {userId} AND bookId = {bookId}")
    if len(cur.fetchall()) != 0:
        return json.dumps({"success": False, "msg": "Book already published!"})

    cur.execute(f"SELECT shareCode FROM BookShare WHERE userId = {userId} AND bookId = {bookId}")
    t = cur.fetchall()
    shareCode = ""
    if len(t) != 0:
        shareCode = "!"+t[0][0]
    
    if shareCode == "":
        return json.dumps({"success": False, "msg": "Book must be shared first before publishing it on Discovery!"})

    discoveryId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 6")
    t = cur.fetchall()
    if len(t) > 0:
        discoveryId = t[0][0]
    cur.execute(f"UPDATE IDInfo SET nextId = {discoveryId + 1} WHERE type = 6")
    
    cur.execute(f"INSERT INTO BookDiscovery VALUES ({discoveryId}, {userId}, {bookId}, '{title}', '{description}')")
    conn.commit()

    msg = "Book published to Discovery. People will be able to find it and import it. All your updates made within this word book will be synced to Discovery."

    return json.dumps({"success": True, "msg": msg, "discoveryId": discoveryId})

@app.route("/api/discovery/book/unpublish", methods = ['POST'])
def apiDiscoveryBookUnpublish():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    discoveryId = int(request.form["discoveryId"])

    cur.execute(f"SELECT * FROM BookDiscovery WHERE discoveryId = {discoveryId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "Book not published!"})

    cur.execute(f"DELETE FROM BookDiscovery WHERE discoveryId = {discoveryId}")
    conn.commit()

    return json.dumps({"success": False, "msg": "Book unpublished!"})

@app.route("/api/discovery/book/update", methods = ['POST'])
def apiDiscoveryBookUpdate():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    discoveryId = int(request.form["discoveryId"])
    title = encode(request.form["title"])
    description = encode(request.form["description"])

    cur.execute(f"SELECT publisherId FROM BookDiscovery WHERE discoveryId = {discoveryId}")
    publisherId = 0
    t = cur.fetchall()
    if len(t) > 0:
        publisherId = t[0][0]
    if publisherId != userId:
        return json.dumps({"success": False, "msg": "You are not the publisher of this post!"})

    cur.execute(f"UPDATE BookDiscovery SET title = '{title}' WHERE discoveryId = {discoveryId}")
    cur.execute(f"UPDATE BookDiscovery SET description = '{description}' WHERE discoveryId = {discoveryId}")
    conn.commit()
    
    return json.dumps({"success": True, "msg": "Success! Discovery post updated!"})

@app.route("/api/discovery/book/like", methods = ['POST'])
def apiDiscoveryBookLike():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    discoveryId = int(request.form["discoveryId"])
    
    cur.execute(f"SELECT publisherId, bookId FROM BookDiscovery WHERE discoveryId = {discoveryId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Book not found!"})
    
    cur.execute(f"SELECT * FROM BookDiscoveryLike WHERE discoveryId = {discoveryId} AND userId = {userId} AND like = 1")
    if len(cur.fetchall()) != 0:
        cur.execute(f"DELETE FROM BookDiscoveryLike WHERE discoveryId = {discoveryId} AND userId = {userId} AND like = 1")
        conn.commit()
        return json.dumps({"success": True, "msg": "Unliked!", "liked": False})
    else:
        cur.execute(f"INSERT INTO BookDiscoveryLike VALUES ({discoveryId}, {userId}, 1)")
        conn.commit()
        return json.dumps({"success": True, "msg": "Liked!", "liked": True})