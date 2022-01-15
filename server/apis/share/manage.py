# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException
import time

from app import app, config
from db import newconn
from functions import *

##########
# Share API
# Manage (Owner manage / Import)

@app.post("/api/share")
async def apiShareBook(request: Request):
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

    if op == "list":
        page = int(form["page"])
        if page <= 0:
            page = 1

        pageLimit = int(form["pageLimit"])
        if pageLimit <= 0:
            pageLimit = 20
        
        if pageLimit > 100:
            return {"success": True, "data": [], "total": 0}

        orderBy = form["orderBy"]
        if not orderBy in ["none", "name", "shareCode", "importCount", "timestamp"]:
            orderBy = "name"

        order = form["order"]
        if not order in ["asc", "desc"]:
            order = "asc"
        l = {"asc": 0, "desc": 1}
        order = l[order]

        search = form["search"]
        if search == "" and orderBy == "none":
            orderBy = "name"

        ret = []
        i2n = {}
        cur.execute(f"SELECT bookId, shareCode, importCount, createTS FROM BookShare WHERE userId = {userId} AND shareType = 0")
        d = cur.fetchall()
        for dd in d:
            name = ""
            if dd[0] in i2n.keys():
                name = i2n[dd[0]]
            else:
                cur.execute(f"SELECT name FROM Book WHERE bookId = {dd[0]}")
                t = cur.fetchall()
                if len(t) == 0:
                    continue
                name = decode(t[0][0])
                i2n[dd[0]] = name
            
            ret.append({"bookId": dd[0], "name": name, "shareCode": "!" + dd[1], "importCount": dd[2], "timestamp": dd[3]})
        
        t = {}
        i = 0
        for dd in ret:
            ok = False
            for tt in dd.keys():
                if search == "" or search in str(dd[tt]):
                    ok = True
                    break
            if not ok:
                continue
            i += 1
            t[str(dd[orderBy]) + "<id>" + str(dd["bookId"]) + str(i)] = dd
            
        ret = []
        if orderBy != "none":
            for key in sorted(t.keys()):
                ret.append(t[key])
        else:
            for key in t.keys():
                ret.append(t[key])
        if order == 1:
            ret = ret[::-1]

        if len(ret) <= (page - 1) * pageLimit:
            return {"success": True, "data": [], "total": (len(ret) - 1) // pageLimit + 1, "totalShare": len(ret)}
        elif len(ret) <= page * pageLimit:
            return {"success": True, "data": ret[(page - 1) * pageLimit :], "total": (len(ret) - 1) // pageLimit + 1, "totalShare": len(ret)}
        else:
            return {"success": True, "data": ret[(page - 1) * pageLimit : page * pageLimit], "total": (len(ret) - 1) // pageLimit + 1, "totalShare": len(ret)}

    elif op == "create":
        bookId = int(form["bookId"])

        cur.execute(f"SELECT * FROM Book WHERE userId = {userId} AND bookId = {bookId}")
        if len(cur.fetchall()) == 0:
            return {"success": False, "msg": "Book not found!"}
        
        cur.execute(f"SELECT shareCode FROM BookShare WHERE userId = {userId} AND bookId = {bookId} AND shareType = 0")
        t = cur.fetchall()
        if len(t) >= 20:
            return {"success": False, "msg": "You can create at most 20 shares for one book!"}
        else:
            shareCode = genCode(8)
            cur.execute(f"SELECT shareCode FROM BookShare WHERE shareCode = '{shareCode}'")
            if len(cur.fetchall()) != 0: # conflict
                for _ in range(30):
                    shareCode = genCode(8)
                    cur.execute(f"SELECT shareCode FROM Book WHERE shareCode = '{shareCode}'")
                    if len(cur.fetchall()) == 0:
                        break
                cur.execute(f"SELECT shareCode FROM Book WHERE shareCode = '{shareCode}'")
                if len(cur.fetchall()) != 0:
                    return {"success": False, "msg": "Unable to generate an unique share code..."}
                    
            cur.execute(f"INSERT INTO BookShare VALUES ({userId}, {bookId}, '{shareCode}', 0, {int(time.time())}, 0)")
            conn.commit()

            return {"success": True, "msg": "A new book share has been created!", "shareCode": "!" + shareCode}

    elif op == "remove":
        code = form["shareCode"]
        code = code.replace("!","").replace("@","")

        if not code.isalnum():
            return {"success": False, "msg": "Invalid share code!"}

        cur.execute(f"SELECT bookId FROM BookShare WHERE userId = {userId} AND shareType = 0 AND shareCode = '{code}'")
        t = cur.fetchall()
        if len(t) == 0:
            return {"success": False, "msg": "Invalid share code!"}
        else:
            cur.execute(f"DELETE FROM BookShare WHERE userId = {userId} AND bookId = {t[0][0]} AND shareCode = '{code}'")
            conn.commit()
            return {"success": True, "msg": "Book unshared!"}

@app.post("/api/share/import")
async def apiShareImport(request: Request):
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

    shareCode = str(form["shareCode"])

    if shareCode.startswith("!"):
        shareCode = shareCode[1:]
    
    if not shareCode.isalnum():
        return {"success": False, "msg": "Invalid share code!"}

    cur.execute(f"SELECT userId, bookId FROM BookShare WHERE shareCode = '{shareCode}'")
    d = cur.fetchall()
    if len(d) != 0:
        sharerUserId = d[0][0]
        sharerBookId = d[0][1]

        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {sharerUserId}")
        if len(cur.fetchall()) == 0:
            return {"success": False, "msg": "Invalid share code!"}
    
        if OPLimit(ip, "import_share", maxop = 10):
            return {"success": False, "msg": "Too many requests! Try again later!"}
        
        sharerUsername = "Unknown"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {sharerUserId}")
        tt = cur.fetchall()
        if len(tt) > 0:
            sharerUsername = decode(tt[0][0])
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
            t = getBookData(sharerUserId, sharerBookId)
        else:
            cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {sharerUserId}")
            ttt = cur.fetchall()
            for tt in ttt:
                t.append(tt[0])

        cur.execute(f"SELECT questionId, question, answer FROM QuestionList WHERE userId = {sharerUserId}")
        b = cur.fetchall()
        di = {}
        for bb in b:
            di[bb[0]] = (bb[1], bb[2])
        
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
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'create_book', {int(time.time())}, '{encode(f'Imported book {decode(name)}')}')")
        
        questionId = 1
        for tt in t:
            # do not use same question to prevent accidental question deletion when new book is deleted
            memorizedTS = 0
            cur.execute(f"SELECT questionId, answer FROM QuestionList WHERE userId = {userId} AND question = '{di[tt][0]}'")
            p = cur.fetchall()
            for pp in p:
                if pp[1] == di[tt][1]: # question completely the same
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

            cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")
            cur.execute(f"INSERT INTO QuestionList VALUES ({userId}, {questionId}, '{di[tt][0]}', '{di[tt][1]}', 1, {memorizedTS})")
            cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{questionId}, 0, -1)")

            updateQuestionStatus(userId, questionId, -1) # -1 is imported question
            #updateQuestionStatus(userId, questionId, 1) # 1 is default status

            questionId += 1
        
        # update import count
        cur.execute(f"UPDATE BookShare SET importCount = importCount + 1 WHERE userId = {userId} AND bookId = {sharerBookId} AND shareCode = '{shareCode}'")
        conn.commit()            

        return {"success": True, "bookId": bookId}
    
    else:
        return {"success": False, "msg": "Invalid share code!"}