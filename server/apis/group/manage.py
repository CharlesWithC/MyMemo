# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import time, json

from app import app, config
from db import newconn
from functions import *

##########
# Group API
# Manage

@app.post("/api/group")
async def apiGroup(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    op = form["operation"]

    if op == "create":
        allow = config.allow_group_creation_for_all_user
        cur.execute(f"SELECT value FROM Privilege WHERE userId = {userId} AND item = 'allow_group_creation'")
        pr = cur.fetchall()
        if len(pr) != 0:
            allow = pr[0][0]
        if not allow:
            return {"success": False, "msg": f"You are not allowed to create groups. Contact administrator for help."}

        bookId = int(form["bookId"])
        if bookId == 0:
            return {"success": False, "msg": "You cannot create a group based on your question database."}
        
        cur.execute(f"SELECT * FROM Book WHERE bookId = {bookId} AND userId = {userId}")
        if len(cur.fetchall()) == 0:
            return {"success": False, "msg": "Book to be used as group book not found!"}

        name = encode(form["name"])
        description = encode(form["description"])

        groupId = 1
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 4")
        t = cur.fetchall()
        if len(t) > 0:
            groupId = t[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {groupId + 1} WHERE type = 4")

        lmt = config.max_group_member
        cur.execute(f"SELECT value FROM Privilege WHERE userId = {userId} AND item = 'group_member_limit'")
        pr = cur.fetchall()
        if len(pr) != 0:
            lmt = pr[0][0]

        if len(name) >= 256:
            return {"success": False, "msg": "Group name too long!"}
        if len(description) >= 2048:
            return {"success": False, "msg": "Description too long!"}

        gcode = genCode(8)
        cur.execute(f"INSERT INTO GroupInfo VALUES ({groupId}, {userId}, '{name}', '{description}', {lmt}, '{gcode}', 0)")
        cur.execute(f"INSERT INTO GroupMember VALUES ({groupId}, {userId}, 1, {bookId})")
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'create_group', {int(time.time())}, '{encode(f'Created group {decode(name)}')}')")
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'join_group', {int(time.time()+1)}, '{encode(f'Joined group {decode(name)}')}')")
        cur.execute(f"UPDATE Book SET name = '{name}' WHERE bookId = {bookId} AND userId = {userId}")

        questions = getBookData(userId, bookId)
        
        gquestionId = 1
        for questionId in questions:
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 5 AND userId = {groupId}")
            d = cur.fetchall()
            if len(d) == 0:
                cur.execute(f"INSERT INTO IDInfo VALUES (5, {groupId}, 2)")
            else:
                gquestionId = d[0][0]
                cur.execute(f"UPDATE IDInfo SET nextId = {gquestionId + 1} WHERE type = 5 AND userId = {groupId}")

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

        return {"success": True, "msg": f"Group created! Group code: @{gcode}.", \
            "groupId": groupId, "groupCode": f"@{gcode}", "isGroupOwner": True}

    elif op == "dismiss":
        groupId = int(form["groupId"])
        cur.execute(f"SELECT owner, name FROM GroupInfo WHERE groupId = {groupId}")
        t = cur.fetchall()
        if len(t) == 0:
            return {"success": False, "msg": f"Group not found!"}
        owner = t[0][0]
        name = t[0][1]

        if owner != userId:
            return {"success": False, "msg": f"You are not the owner of the group!"}
            
        cur.execute(f"SELECT * FROM Discovery WHERE publisherId = {userId} AND bookId = {groupId} AND type = 2")
        if len(cur.fetchall()) != 0:
            return {"success": False, "msg": f"Group published to Discovery! Unpublish it before dismissing it!"}
        
        cur.execute(f"DELETE FROM GroupInfo WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupQuestion WHERE groupId = {groupId}")
        cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId}")
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'quit_group', {int(time.time())}, '{encode(f'Quit group {decode(name)}')}')")
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'delete_group', {int(time.time()+1)}, '{encode(f'Deleted group {decode(name)}')}')")
        conn.commit()

        return {"success": True, "msg": f"Group dismissed! Book sync stopped and members are not able to see others' progress."}

@app.post("/api/group/manage")
async def apiManageGroup(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    groupId = int(form["groupId"])
    
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Group does not exist!"}
    owner = d[0][0]
    if userId != owner:
        return {"success": False, "msg": "You are not the owner of the group!"}
    
    op = form["operation"]
    if op == "makeEditor":
        users = json.loads(form["users"])
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
                    editorName = decode(t[0][0])
                if editorName == "@deleted":
                    continue
                
                cur.execute(f"UPDATE GroupMember SET isEditor = 1 WHERE groupId = {groupId} AND userId = {uid}")
        conn.commit()
        return {"success": True, "msg": "Group editor updated!"}

    elif op == "kick":
        cur.execute(f"SELECT name FROM GroupInfo WHERE groupId = {groupId}")
        t = cur.fetchall()
        name = ''
        if len(t) > 0:
            name = t[0][0]
        users = json.loads(form["users"])
        for uid in users:
            if uid == userId:
                continue
            cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {uid}")
            cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {uid}")
            cur.execute(f"INSERT INTO UserEvent VALUES ({uid}, 'quit_group', {int(time.time())}, '{encode(f'You have been kicked from group {decode(name)}')}')")
        conn.commit()
        return {"success": True, "msg": "Group member kicked!"}
    
    elif op =="transferOwnership":
        users = json.loads(form["users"])
        if len(users) != 1:
            return {"success": True, "msg": "Make sure you only selected one user!"}
        uid = users[0]
        if uid == userId:
            return {"success": True, "msg": "You are already the owner!"}
        cur.execute(f"SELECT isEditor FROM GroupMember WHERE groupId = {groupId} AND userId = {uid}")
        t = cur.fetchall()
        if len(t) == 0 or t[0][0] == 0:
            return {"success": False, "msg": "Member not in group or member not an editor. Make sure the new owner is already in group and you have made him / her an editor."}
        
        newOwner = "@deleted"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
        t = cur.fetchall()
        if len(t) != 0:
            newOwner = decode(t[0][0])
        if newOwner == "@deleted":
            return {"success": False, "msg": f"You cannot transfer ownership to a deleted user!"}

        cur.execute(f"UPDATE GroupInfo SET owner = {uid} WHERE groupId = {groupId}")
        cur.execute(f"UPDATE GroupMember SET isEditor = 1 WHERE groupId = {groupId} and userId = {uid}")
        conn.commit()
        return {"success": True, "msg": f"Ownership transferred to {newOwner} (UID: {uid})"}

    elif op == "updateInfo":
        name = encode(form["name"])
        description = encode(form["description"])

        if len(name) >= 256:
            return {"success": False, "msg": "Group name too long!"}
        if len(description) >= 2048:
            return {"success": False, "msg": "Description too long!"}

        cur.execute(f"UPDATE GroupInfo SET name = '{name}' WHERE groupId = {groupId}")
        cur.execute(f"UPDATE GroupInfo SET description = '{description}' WHERE groupId = {groupId}")
        cur.execute(f"SELECT userId, bookId FROM GroupMember WHERE groupId = {groupId}")
        binds = cur.fetchall()
        for bind in binds:
            uid = bind[0]
            wbid = bind[1]

            if len(name) >= 256:
                return {"success": False, "msg": "Book name too long!"}

            cur.execute(f"UPDATE Book SET name = '{name}' WHERE bookId = {wbid} AND userId = {uid}")
        conn.commit()

        return {"success": True, "msg": f"Group information updated!"}
    
    elif op == "anonymous":
        anonymous = int(form["anonymous"])
        if not anonymous in [0, 1, 2]:
            return {"success": False, "msg": f"Invalid anonymous status!"}

        cur.execute(f"SELECT anonymous FROM GroupInfo WHERE groupId = {groupId}")
        t = cur.fetchall()
        if len(t) > 0:
            cur.execute(f"UPDATE GroupInfo SET anonymous = {anonymous} WHERE groupId = {groupId}")
            conn.commit()
            return {"success": True, "msg": f"Group anonymous settings updated", "anonymous": anonymous}
        
        return {"success": False, "msg": f"Group not found!"}

@app.post("/api/group/code/update")
async def apiGroupCodeUpdate(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    groupId = int(form["groupId"])
    
    cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Group does not exist!"}
    owner = d[0][0]
    if userId != owner:
        return {"success": False, "msg": "You are not the owner of the group!"}

    op = form["operation"]

    if op == "disable":
        cur.execute(f"UPDATE GroupInfo SET groupCode = 'pvtgroup' WHERE groupId = {groupId}")
        conn.commit()
        return {"success": True, "msg": "Group has been made to private and no user is allowed to join!", "groupCode": "@pvtgroup"}
    
    elif op == "revoke":
        gcode = genCode(8)
        cur.execute(f"UPDATE GroupInfo SET groupCode = '{gcode}' WHERE groupId = {groupId}")
        conn.commit()
        return {"success": True, "msg": f"New group code: @{gcode}", "groupCode": f"@{gcode}"}

@app.post("/api/group/join")
async def apiJoinGroup(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    groupCode = form["groupCode"]

    if groupCode.startswith("@"):
        groupCode = groupCode[1:]

    if not groupCode.isalnum():
        return {"success": False, "msg": "Invalid group code!"}

    if groupCode == "pvtgroup":
        return {"success": False, "msg": "This is the general code of all private code and it cannot be used!"}
        
    cur.execute(f"SELECT groupId, name FROM GroupInfo WHERE groupCode = '{groupCode}'")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
        name = d[0][1]

        cur.execute(f"SELECT userId FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        if len(cur.fetchall()) != 0:
            return {"success": False, "msg": "You have already joined this group!"}
        
        cur.execute(f"SELECT owner FROM GroupInfo WHERE groupId = {groupId}")
        owner = 0
        t = cur.fetchall()
        if len(t) > 0:
            owner = t[0][0]
            cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {owner}")
            if len(cur.fetchall()) == 0:
                return {"success": False, "msg": "Invalid group code!"}
        else:
            return {"success": False, "msg": "Invalid group code!"}
            
        mlmt = 0
        cur.execute(f"SELECT memberLimit FROM GroupInfo WHERE groupId = {groupId}")
        tt = cur.fetchall()
        if len(tt) > 0:
            mlmt = tt[0][0]
        cur.execute(f"SELECT * FROM GroupMember WHERE groupId = {groupId}")
        if len(cur.fetchall()) >= mlmt:
            return {"success": False, "msg": "Group is full!"}

        cur.execute(f"SELECT question, answer, groupQuestionId FROM GroupQuestion WHERE groupId = {groupId}")
        t = cur.fetchall()
        
        # preserve limit check here as if the owner dismissed the group, the questions will remain in users' lists
        max_allow = config.max_question_per_user_allowed
        cur.execute(f"SELECT value FROM Privilege WHERE userId = {userId} AND item = 'question_limit'")
        pr = cur.fetchall()
        if len(pr) != 0:
            max_allow = pr[0][0]
        cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) != 0 and max_allow != -1 and d[0][0] + len(t) >= max_allow:
            return {"success": False, "msg": f"You have reached your limit of maximum added questions {max_allow}. Remove some old questions or contact administrator for help."}

        max_book_allow = config.max_book_per_user_allowed
        cur.execute(f"SELECT value FROM Privilege WHERE userId = {userId} AND item = 'book_limit'")
        pr = cur.fetchall()
        if len(pr) != 0:
            max_book_allow = pr[0][0]
        cur.execute(f"SELECT COUNT(*) FROM Book WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) != 0 and max_book_allow != -1 and d[0][0] + 1 >= max_book_allow:
            return {"success": False, "msg": f"You have reached your limit of maximum created book {max_allow}. Remove some books (this will not remove the questions) or contact administrator for help."}

        bookId = 1
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 3 AND userId = {userId}")
        d = cur.fetchall()
        if len(d) == 0:
            cur.execute(f"INSERT INTO IDInfo VALUES (3, {userId}, 2)")
        else:
            bookId = d[0][0]
            cur.execute(f"UPDATE IDInfo SET nextId = {bookId + 1} WHERE type = 3 AND userId = {userId}")

        # do import
        cur.execute(f"INSERT INTO Book VALUES ({userId}, {bookId}, '{name}', 0)")
        cur.execute(f"INSERT INTO GroupMember VALUES ({groupId}, {userId}, 0, {bookId})")
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'join_group', {int(time.time())}, '{encode(f'Joined group {decode(name)}')}')")

        questionId = 1
        for tt in t:
            # do not use same question to prevent accidental question deletion when new book is deleted
            cur.execute(f"SELECT questionId, answer FROM QuestionList WHERE userId = {userId} AND question = '{tt[0]}'")
            p = cur.fetchall()
            memorizedTS = 0
            for pp in p:
                if pp[1] == tt[1]: # question completely the same
                    cur.execute(f"SELECT memorizedTimestamp FROM QuestionList WHERE userId = {userId} AND questionId = {pp[0]}")
                    k = cur.fetchall()
                    if len(k) != 0 and k[0][0] != 0:
                        memorizedTS = k[0][0]
                        cur.execute(f"UPDATE Book SET progress = progress + 1 WHERE userId = {userId} AND bookId = {bookId}")
                    break

            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
            d = cur.fetchall()
            if len(d) == 0:
                cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
            else:
                questionId = d[0][0]
                cur.execute(f"UPDATE IDInfo SET nextId = {questionId + 1} WHERE type = 2 AND userId = {userId}")

            # no duplicate check as user are not allowed to edit questions in group
            cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")
            cur.execute(f"INSERT INTO QuestionList VALUES ({userId}, {questionId}, '{tt[0]}', '{tt[1]}', 1, {memorizedTS})")
            cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{questionId}, 0, -1)")
            cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {userId}, {questionId}, {tt[2]})")

            updateQuestionStatus(userId, questionId, -1) # -1 is imported question
            # updateQuestionStatus(userId, questionId, 1) # 1 is default status

            questionId += 1
        
        conn.commit()
        return {"success": True, "bookId": bookId}
    
    else:
        return {"success": False, "msg": "Invalid group code!"}

@app.post("/api/group/quit")
async def apiQuitGroup(request: Request):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)

    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)
    
    groupId = int(form["groupId"])

    cur.execute(f"SELECT * FROM GroupMember WHERE userId = {userId} AND groupId = {groupId}")
    if len(cur.fetchall()) == 0:
        return {"success": False, "msg": "You are not in the group!"}
    
    cur.execute(f"SELECT owner, name FROM GroupInfo WHERE groupId = {groupId}")
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Group does not exist!"}
    owner = d[0][0]
    if userId == owner:
        return {"success": False, "msg": "You are the owner of the group. You have to transfer group ownership before quiting the group."}
    name = d[0][1]

    cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {userId}")
    cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'quit_group', {int(time.time())}, '{encode(f'Quit group {decode(name)}')}')")

    conn.commit()

    return {"success": True, "msg": "You have quit the group successfully! The book has became a local one."}