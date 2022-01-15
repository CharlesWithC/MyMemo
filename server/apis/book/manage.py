# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import time

from app import app, config
from db import newconn
from functions import *

##########
# Book API
# Manage (Create, Clone, Delete, Rename, Share)

@app.post("/api/book/create")
async def apiCreateBook(request: Request):
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

    if OPLimit(ip, "create_book", maxop = 10):
        return {"success": False, "msg": "Too many requests! Try again later!"}
    
    name = str(form["name"])
    name = encode(name)
    
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
    
    if len(name) >= 256:
        return {"success": False, "msg": "Book name too long!"}

    cur.execute(f"INSERT INTO Book VALUES ({userId}, {bookId}, '{name}', 0)")
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'create_book', {int(time.time())}, '{encode(f'Created book {decode(name)}')}')")
    conn.commit()
    
    return {"success": True}

@app.post("/api/book/clone")
async def apiCloneBook(request: Request):
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
    
    cloneFrom = int(form["fromBook"])

    cur.execute(f"SELECT name FROM Book WHERE bookId = {cloneFrom} AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        return {"success": False, "msg": "Book to clone from not found!"}
    name = encode(decode(d[0][0]) + " (Clone)")
    
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

    d = getBookData(userId, cloneFrom)

    max_allow = config.max_question_per_user_allowed
    cur.execute(f"SELECT value FROM Privilege WHERE userId = {userId} AND item = 'question_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_allow != -1 and d[0][0] + len(d) >= max_allow:
        return {"success": False, "msg": f"Your max question limit is {max_allow} and after cloing the book you will exceed the limit so operation is aborted!"}

    cur.execute(f"SELECT progress FROM Book WHERE userId = {userId} AND bookId = {cloneFrom}")
    t = cur.fetchall()
    progress = 0
    if len(t) > 0:
        progress = t[0][0]
    cur.execute(f"INSERT INTO Book VALUES ({userId}, {bookId}, '{name}', 0)")
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'create_book', {int(time.time())}, '{encode(f'Created book {decode(name)}')}')")
    
    cur.execute(f"SELECT * FROM QuestionList WHERE userId = {userId}")
    l = cur.fetchall()
    dt = {}
    for ll in l:
        dt[ll[1]] = ll

    d = getBookData(userId, cloneFrom)
    for dd in d:
        wid = 1
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
        p = cur.fetchall()
        if len(p) == 0:
            cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
        else:
            wid = p[0][0]
            cur.execute(f"UPDATE IDInfo SET nextId = {wid + 1} WHERE type = 2 AND userId = {userId}")
        p = dt[dd]
        cur.execute(f"INSERT INTO QuestionList VALUES ({userId}, {wid}, '{p[2]}', '{p[3]}', {p[4]}, {p[5]})")
        cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {wid})")
    
    conn.commit()
    return {"success": True, "msg": "Book cloned!"}
    

@app.post("/api/book/delete")
async def apiDeleteBook(request: Request):
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
    
    bookId = int(form["bookId"])
    cur.execute(f"SELECT name FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "Book does not exist!"}
    name = t[0][0]

    cur.execute(f"SELECT * FROM Discovery WHERE publisherId = {userId} AND bookId = {bookId} AND type = 1")
    if len(cur.fetchall()) != 0:
        return {"success": False, "msg": "Book published to Discovery! Unpublish it first before deleting the book."}
            
    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupMember WHERE userId = {userId} AND bookId = {bookId}")
    d = cur.fetchall()
    if len(d) != 0:
        groupId = d[0][0]
    
    if groupId != -1:
        cur.execute(f"SELECT owner, name FROM GroupInfo WHERE groupId = {groupId}")
        d = cur.fetchall()
        if len(d) == 0:
            return {"success": False, "msg": "Group does not exist!"}
        owner = d[0][0]
        if userId == owner:
            return {"success": False, "msg": "You are the owner of the group. You have to transfer group ownership or dismiss the group before deleting the book."}
        name = d[0][1]
        
        cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"DELETE FROM GroupMember WHERE groupId = {groupId} AND userId = {userId}")
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'quit_group', {int(time.time())}, '{encode(f'Quit group {decode(name)}')}')")
    
    removeAll = form["removeAll"]
    if removeAll:
        qs = getBookData(userId, bookId)
        for q in qs:
            cur.execute(f"DELETE FROM BookData WHERE userId = {userId} AND questionId = {q}")
            cur.execute(f"DELETE FROM QuestionList WHERE questionId = {q} AND userId = {userId}")

    cur.execute(f"DELETE FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'delete_book', {int(time.time())}, '{encode(f'Deleted book {decode(name)}')}')")
    cur.execute(f"DELETE FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    conn.commit()

    return {"success": True}

@app.post("/api/book/rename")
async def apiRenameBook(request: Request):
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
    
    bookId = int(form["bookId"])
    newName = str(form["name"])

    groupId = -1
    cur.execute(f"SELECT groupId FROM GroupMember WHERE bookId = {bookId} AND userId = {userId}")
    t = cur.fetchall()
    if len(t) != 0:
        groupId = t[0][0]
        gname = "Unknown Book"
        cur.execute(f"SELECT name FROM GroupInfo WHERE groupId = {groupId}")
        tt = cur.fetchall()
        if len(tt) > 0:
            gname = tt[0][0]
        
        if len(gname) >= 256:
            return {"success": False, "msg": "Book name too long!"}

        cur.execute(f"UPDATE Book SET name = '{gname}' WHERE userId = {userId} AND bookId = {bookId}")
        conn.commit()
        return {"success": False, "msg": "You are not allowed to rename a book that is bound to a group!"}

    cur.execute(f"SELECT * FROM Book WHERE userId = {userId} AND bookId = {bookId}")
    if len(cur.fetchall()) == 0:
        return {"success": False, "msg": "Book does not exist!"}

    if len(encode(newName)) >= 256:
        return {"success": False, "msg": "Book name too long!"}

    cur.execute(f"UPDATE Book SET name = '{encode(newName)}' WHERE userId = {userId} AND bookId = {bookId}")
    conn.commit()
    return {"success": True}