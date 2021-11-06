# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort, send_file
import os, sys, datetime, time, math
import random, uuid
import json
import validators
import sqlite3
import pandas as pd

from app import app, config
from functions import *
import sessions

##########
# Group API

@app.route("/api/group", methods = ['POST'])
def apiGroup():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    op = request.form["operation"]

    if op == "create":
        allow = config.allow_group_creation_for_all_user
        cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'allow_group_creation'")
        pr = cur.fetchall()
        if len(pr) != 0:
            allow = pr[0][0]
        if not allow:
            return json.dumps({"success": False, "msg": f"You are not allowed to create groups. Contact administrator for help."})

        bookId = int(request.form["bookId"])
        if bookId == 0:
            return json.dumps({"success": False, "msg": "You cannot create a group based on your question database."})
        
        cur.execute(f"SELECT * FROM Book WHERE bookId = {bookId} AND userId = {userId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"success": False, "msg": "Book to be used as group book not found!"})

        name = encode(request.form["name"])
        description = encode(request.form["description"])

        groupId = 1
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 4")
        t = cur.fetchall()
        if len(t) > 0:
            groupId = t[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {groupId + 1} WHERE type = 4")

        lmt = config.max_group_member
        cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'group_member_limit'")
        pr = cur.fetchall()
        if len(pr) != 0:
            lmt = pr[0][0]

        gcode = genCode(8)
        cur.execute(f"INSERT INTO GroupInfo VALUES ({groupId}, {userId}, '{name}', '{description}', {lmt}, '{gcode}')")
        cur.execute(f"INSERT INTO GroupMember VALUES ({groupId}, {userId}, 1)")
        cur.execute(f"INSERT INTO GroupBind VALUES ({groupId}, {userId}, {bookId})")
        cur.execute(f"SELECT questionId FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
        questions = cur.fetchall()
        
        gquestionId = 1
        for question in questions:
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 5 AND userId = {groupId}")
            d = cur.fetchall()
            if len(d) == 0:
                cur.execute(f"INSERT INTO IDInfo VALUES (5, {groupId}, 2)")
            else:
                gquestionId = d[0][0]
                cur.execute(f"UPDATE IDInfo SET nextId = {gquestionId + 1} WHERE type = 5 AND userId = {groupId}")

            questionId = question[0]
            cur.execute(f"SELECT question, answer FROM QuestionList WHERE userId = {userId} AND questionId = {questionId}")
            t = cur.fetchall()
            if len(t) > 0:
                d = t[0]
                cur.execute(f"INSERT INTO GroupQuestion VALUES ({groupId}, {gquestionId}, '{d[0]}', '{d[1]}')")
                cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {questionId}, {gquestionId})")
            else:
                continue
            gquestionId += 1
        
        conn.commit()

        return json.dumps({"success": True, "msg": f"Group created! Group code: @{gcode}. Tell your friends to create a book with this code and they will join your group automatically.", \
            "groupId": groupId, "groupCode": f"@{gcode}", "isGroupOwner": True})

    elif op == "dismiss":
        groupId = int(request.form["groupId"])
        cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
        owner = cur.fetchall()
        if len(owner) == 0:
            return json.dumps({"success": False, "msg": f"Group not found!"})
        owner = owner[0][0]

        if owner != userId:
            return json.dumps({"success": False, "msg": f"You are not the owner of the group!"})
        
        cur.execute(f"DELETE FROM GroupInfo WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupQuestion WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId}")
        conn.commit()

        return json.dumps({"success": True, "msg": f"Group dismissed! Book sync stopped and members are not able to see others' progress."})

@app.route("/api/group/quit", methods = ['POST'])
def apiQuitGroup():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    groupId = int(request.form["groupId"])

    cur.execute(f"SELECT * FROM GroupMember WHERE userId = {userId} AND groupId = {groupId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"success": False, "msg": "You are not in the group!"})
    
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Group does not exist!"})
    owner = d[0][0]
    if userId == owner:
        return json.dumps({"success": False, "msg": "You are the owner of the group. You have to transfer group ownership before quiting the group."})

    cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {userId}")
    cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
    cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId} AND userId = {userId}")

    conn.commit()

    return json.dumps({"success": True, "msg": "You have quit the group successfully! The book has became a local one."})

@app.route("/api/group/code/update", methods = ['POST'])
def apiGroupCodeUpdate():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    groupId = int(request.form["groupId"])
    
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Group does not exist!"})
    owner = d[0][0]
    if userId != owner:
        return json.dumps({"success": False, "msg": "You are not the owner of the group!"})

    op = request.form["operation"]

    if op == "disable":
        cur.execute(f"UPDATE GroupInfo SET groupCode = 'pvtgroup' WHERE groupId = {groupId}")
        conn.commit()
        return json.dumps({"success": True, "msg": "Group has been made to private and no user is allowed to join!", "groupCode": "@pvtgroup"})
    
    elif op == "revoke":
        gcode = genCode(8)
        cur.execute(f"UPDATE GroupInfo SET groupCode = '{gcode}' WHERE groupId = {groupId}")
        conn.commit()
        return json.dumps({"success": True, "msg": f"New group code: @{gcode}", "groupCode": f"@{gcode}"})

@app.route("/api/group/member", methods = ['POST'])
def apiGroupMember():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    groupId = int(request.form["groupId"])
    cur.execute(f"SELECT userId, isEditor FROM GroupMember WHERE groupId = {groupId}")
    d = cur.fetchall()
    if not (userId,0,) in d and not (userId,1,) in d:
        return json.dumps({"success": False, "msg": f"You must be a member of the group before viewing its members."})
    
    cur.execute(f"SELECT * FROM GroupQuestion WHERE groupId = {groupId}")
    questioncnt = len(cur.fetchall())
    cur.execute(f"SELECT groupQuestionId FROM GroupQuestion WHERE groupId = {groupId}")
    questions = cur.fetchall()

    info = None
    cur.execute(f"SELECT name, description FROM GroupInfo WHERE groupId = {groupId}")
    t = cur.fetchall()
    if len(t) > 0:
        info = t[0]
    else:
        return json.dumps({"success": False, "msg": "Group not found!"})

    owner = 0
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    t = cur.fetchall()
    if len(t) > 0:
        owner = t[0][0]
        if owner < 0:
            return json.dumps({"success": False, "msg": "Group is invisible because its owner is banned."})
    
    isOwner = False
    if owner == userId:
        isOwner = True

    ret = []
    for dd in d:
        uid = dd[0]
        isEditor = dd[1]

        if uid < 0:
            continue
        
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
        t = cur.fetchall()
        if len(t) == 0:
            continue
        
        username = t[0][0]

        if owner == uid:
            username = username + " (Owner)"
        elif isEditor:
            username = username + " (Editor)"
        
        bookId = -1
        cur.execute(f"SELECT bookId FROM GroupBind WHERE groupId = {groupId} AND userId = {uid}")
        t = cur.fetchall()
        if len(t) > 0:
            bookId = t[0][0]
        cur.execute(f"SELECT progress FROM BookProgress WHERE userId = {uid} AND bookId = {bookId}")
        p = cur.fetchall()
        pgs = 0
        if len(p) != 0:
            pgs = p[0][0]
        
        pgs = f"{pgs} / {questioncnt}"

        ret.append({"userId": uid, "username": username, "progress": pgs})
    
    return json.dumps({"name": decode(info[0]), "description": decode(info[1]), "member": ret, "isOwner": isOwner})

@app.route("/api/group/manage", methods = ['POST'])
def apiManageGroup():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    groupId = int(request.form["groupId"])
    
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return json.dumps({"success": False, "msg": "Group does not exist!"})
    owner = d[0][0]
    if userId != owner:
        return json.dumps({"success": False, "msg": "You are not the owner of the group!"})
    
    op = request.form["operation"]
    if op == "makeEditor":
        users = json.loads(request.form["users"])
        for uid in users:
            if uid == userId:
                continue

            cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {uid}")
            t = cur.fetchall()
            if len(t) == 0:
                continue
            if t[0][0] == 1:
                cur.execute(f"UPDATE GroupMember SET isEditor = 0 WHERE groupId = {groupId} AND userId = {uid}")            
            elif t[0][0] == 0:
                editorName = "@deleted"
                cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
                t = cur.fetchall()
                if len(t) != 0:
                    editorName = t[0][0]
                if editorName == "@deleted":
                    continue
                
                cur.execute(f"UPDATE GroupMember SET isEditor = 1 WHERE groupId = {groupId} AND userId = {uid}")
        conn.commit()
        return json.dumps({"success": True, "msg": "Success!"})

    elif op == "kick":
        users = json.loads(request.form["users"])
        for uid in users:
            if uid == userId:
                continue
            cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {uid}")
            cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {uid}")
            cur.execute(f"DELETE FROM GroupBind WHERE groupId = {groupId} AND userId = {uid}")
        conn.commit()
        return json.dumps({"success": True, "msg": "Success!"})
    
    elif op =="transferOwnership":
        users = json.loads(request.form["users"])
        if len(users) != 1:
            return json.dumps({"success": True, "msg": "Make sure you only selected one user!"})
        uid = users[0]
        if uid == userId:
            return json.dumps({"success": True, "msg": "You are already the owner!"})
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {uid}")
        t = cur.fetchall()
        if len(t) == 0 or t[0][0] == 0:
            return json.dumps({"success": False, "msg": "Member not in group or member not an editor. Make sure the new owner is already in group and you have made him / her an editor."})
        
        newOwner = "@deleted"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
        t = cur.fetchall()
        if len(t) != 0:
            newOwner = t[0][0]
        if newOwner == "@deleted":
            return json.dumps({"success": False, "msg": f"You cannot transfer ownership to a deleted user!"})

        cur.execute(f"UPDATE GroupInfo SET owner = {uid} WHERE groupId = {groupId}")
        cur.execute(f"UPDATE GroupMember SET isEditor = 1 WHERE groupId = {groupId} and userId = {uid}")
        conn.commit()
        return json.dumps({"success": True, "msg": f"Success! Ownership transferred to UID {uid}"})

    elif op == "updateInfo":
        name = encode(request.form["name"])
        description = encode(request.form["description"])
        cur.execute(f"UPDATE GroupInfo SET name = '{name}' WHERE groupId = {groupId}")
        cur.execute(f"UPDATE GroupInfo SET description = '{description}' WHERE groupId = {groupId}")
        cur.execute(f"SELECT userId, bookId FROM GroupBind WHERE groupId = {groupId}")
        binds = cur.fetchall()
        for bind in binds:
            uid = bind[0]
            wbid = bind[1]
            cur.execute(f"UPDATE Book SET name = '{name}' WHERE bookId = {wbid} AND userId = {uid}")
        conn.commit()

        return json.dumps({"success": True, "msg": f"Success! Group information updated!"})