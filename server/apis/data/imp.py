# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks
import time
import pandas as pd
import io

from app import app, config
from db import newconn
from functions import *

##########
# Data API
# Import

lastop = {}
threads = 0
dataUploadResult = {}

def clearOutdated():
    global dataUploadResult
    
    t = list(dataUploadResult.keys())
    for userId in t:
        if not token in dataUploadResult.keys():
            continue
        if time.time() - dataUploadResult[userId][1] >= 120:
            del dataUploadResult[userId]
                
def importWork(userId, bookId, updateType, checkDuplicate, newlist):
    global threads
    threads += 1
        
    conn = newconn()
    cur = conn.cursor()

    newlist.drop_duplicates(subset = ['Question', 'Answer'], ignore_index = True, inplace = True)

    importDuplicate = []
    cur.execute(f"SELECT question FROM QuestionList WHERE userId = {userId}")
    questionList = cur.fetchall()
    for i in range(0, len(newlist)):
        if (encode(str(newlist["Question"][i])),) in questionList:
            importDuplicate.append(str(newlist["Question"][i]))

    if checkDuplicate and updateType == "append":
        if len(importDuplicate) != 0:
            return f"Upload rejected due to duplicated questions: {' ; '.join(importDuplicate)}"
            
    max_allow = config.max_question_per_user_allowed
    cur.execute(f"SELECT value FROM Privilege WHERE userId = {userId} AND item = 'question_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_allow != -1 and d[0][0] + len(newlist) >= max_allow:
        return f"You have reached your limit of maximum added questions {max_allow}. Remove some old questions or contact administrator for help."

    questionId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
    else:
        questionId = d[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {questionId + 1} WHERE type = 2 AND userId = {userId}")
            
    bookList = []
    if bookId != 0:
        cur.execute(f"SELECT bookId FROM Book WHERE userId = {userId} AND bookId = {bookId}")
        if len(cur.fetchall()) == 0:
            bookId = 0
        else:
            bookList = getBookData(userId, bookId)

    groupId = -1
    if bookId != 0:
        groupId = -1
        cur.execute(f"SELECT groupId, isEditor FROM GroupMember WHERE userId = {userId} AND bookId = {bookId}")
        d = cur.fetchall()
        if len(d) != 0:
            groupId = d[0][0]
            isEditor = d[0][1]
            if isEditor == 0:
                return "You are not allowed to edit this question in group as you are not an editor! Clone the book to edit!"

    if updateType  == "clear_overwrite":
        if bookId == 0:
            cur.execute(f"DELETE FROM BookData WHERE userId = {userId}")
            cur.execute(f"DELETE FROM QuestionList WHERE userId = {userId}")
        else:
            t = getBookData(userId, bookId)
            cur.execute(f"DELETE FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
            for tt in t:
                cur.execute(f"DELETE FROM QuestionList WHERE userId = {userId} AND questionId = {tt}")

        if groupId != -1:
            cur.execute(f"SELECT userId, questionIdOfUser FROM GroupSync WHERE groupId = {groupId}")
            t = cur.fetchall()
            for tt in t:
                uid = tt[0]
                qid = tt[1]
                cur.execute(f"DELETE FROM QuestionList WHERE userId = {uid} AND questionId = {qid}")
                cur.execute(f"SELECT bookId FROM GroupMember WHERE userId = {uid} AND groupId = {groupId}")
                p = cur.fetchall()
                if len(p) == 0:
                    continue
                cur.execute(f"DELETE FROM BookData WHERE userId = {uid} AND bookId = {p[0][0]} AND questionId = {qid}")
            cur.execute(f"DELETE FROM GroupQuestion WHERE groupId = {groupId}")
            cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId}")
    
    conn.commit()

    StatusTextToStatus = {"Default": 1, "Tagged": 2, "Deleted": 3}

    groupMember = None
    if groupId != -1:
        cur.execute(f"SELECT userId, bookId FROM GroupMember WHERE groupId = {groupId}")
        groupMember = cur.fetchall()
    
    cur.execute(f"SELECT question, questionId FROM QuestionList WHERE userId = {userId}")
    qlist = cur.fetchall()

    progress = 0
    global dataUploadResult
    for i in range(0, len(newlist)):
        question = str(newlist['Question'][i]).replace("\\n","\n")
        answer = str(newlist['Answer'][i]).replace("\\n","\n")
        if int(i / len(newlist) * 100) > progress:
            progress = int(i / len(newlist) * 100)
            dataUploadResult[userId] = (f'Progress{progress}', time.time())

        if question in importDuplicate and updateType == "overwrite":
            wid = -1
            for q in qlist:
                if q[0] == encode(question):
                    wid = q[1]
            
            if wid != -1:
                if len(encode(answer)) >= 40960:
                    return "Answer too long: " + answer

                cur.execute(f"UPDATE QuestionList SET answer = '{encode(answer)}' WHERE questionId = {wid} AND userId = {userId}")
                if list(newlist.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Deleted"]:
                    status = StatusTextToStatus[newlist["Status"][i]]
                    cur.execute(f"UPDATE QuestionList SET status = {status} WHERE questionId = {wid} AND userId = {userId}")
                if bookId != 0 and not questionId in bookList:
                    cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")
                    bookList.append(questionId)
                    
                continue

        questionId += 1
        updateQuestionStatus(userId, questionId, -1)

        status = 1
        if list(newlist.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Deleted"]:
            status = StatusTextToStatus[newlist["Status"][i]]
            updateQuestionStatus(userId, questionId, status)
        # else:
        #     status = 1
        #     updateQuestionStatus(userId, questionId, status)
            
        if len(encode(question)) >= 40960:
            return "Question too long:" + question
        if len(encode(answer)) >= 40960:
            return "Answer too long:" + answer
        
        cur.execute(f"INSERT INTO QuestionList VALUES ({userId}, {questionId}, '{encode(question)}', '{encode(answer)}', {status}, 0)")
        cur.execute(f"INSERT INTO ChallengeData VALUES ({userId}, {questionId}, 0, -1)")
        cur.execute(f"UPDATE IDInfo SET nextId = {questionId + 1} WHERE type = 2 AND userId = {userId}")
        
        if bookId != 0:
            cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")

            if groupId != -1:
                question = encode(question)
                answer = encode(answer)

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
                
                for tt in groupMember:
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

                    cur.execute(f"INSERT INTO QuestionList VALUES ({uid}, {wid}, '{question}', '{answer}', 1, 0)")
                    cur.execute(f"INSERT INTO BookData VALUES ({uid}, {wbid}, {wid})")
                    cur.execute(f"INSERT INTO ChallengeData VALUES ({uid},{wid},0,-1)")
                    cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {uid}, {wid}, {gquestionId})")
                    updateQuestionStatus(uid, wid, -3) # -3 is group question
                    # updateQuestionStatus(uid, wid, 1) # 1 is default status

    conn.commit()
    threads -= 1
    return "Success"

def importWorkGate(userId, bookId, updateType, checkDuplicate, newlist):
    conn = newconn()
    cur = conn.cursor()
    
    global lastop

    res = ""
    try:
        res = importWork(userId, bookId, updateType, checkDuplicate, newlist)
            
        if not "Success" in res:
            res = "Failed<br>" + res
            if userId in lastop.keys():
                del lastop[userId]
    except:
        res = "Failed"
        if userId in lastop.keys():
            del lastop[userId]
    
    global dataUploadResult
    dataUploadResult[userId] = (res, time.time())

@app.post("/api/data/import")
async def apiImportData(request: Request, background_tasks: BackgroundTasks):
    clearOutdated()
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
    
    if "getResult" in form.keys():
        if userId in dataUploadResult.keys():
            t = dataUploadResult[userId]
            if t[0] != '':
                if t[0].find("Failed") != -1:
                    del dataUploadResult[userId]
                    return {"success": True, "status": 0, "msg": t[0]}
                elif t[0] == "Success":
                    del dataUploadResult[userId]
                    return {"success": True, "status": 1, "msg": "Success"}
                elif t[0].startswith("Progress"):
                    progress = t[0].replace("Progress","")
                    return {"success": True, "status": 2, "msg": f"{progress}% Finished"}
                else:
                    return {"success": True, "status": 2, "msg": t[0]}
            else:
                return {"status": 2, "msg": "Still working on it... <i class='fa fa-spinner fa-spin'></i>"}
        return {"status": 0, "msg": "Upload result has been cleared!"}

    if userId in dataUploadResult.keys():
        return {"success": False, "msg": "Another upload task is running!"}

    # Do file check
    f = form["file"]
    if f.filename == '':
        return {"success": False, "msg": "Invalid import! E2: Empty file name"}

    if not f.filename.endswith(".xlsx"):
        return {"success": False, "msg": "Only .xlsx files are supported!"}
    
    ts = int(time.time())

    buf = io.BytesIO()
    content = await f.read()
    buf.write(content)
    buf.seek(0)
    newlist = None

    try:
        newlist = pd.read_excel(buf, engine = "openpyxl")
        if list(newlist.keys()).count("Question") != 1 or list(newlist.keys()).count("Answer")!=1:
            return {"success": False, "msg": "Invalid format! The columns must contain 'Question','Answer'!"}
    except:
        return {"success": False, "msg": "Invalid format! The columns must contain 'Question','Answer'!"}
    
    updateType = form["updateType"]
    yesno = {"yes": True, "no": False}
    checkDuplicate = form["checkDuplicate"]
    checkDuplicate = yesno[checkDuplicate]

    bookId = int(form["bookId"])
    
    global lastop
    if userId in lastop.keys():
        if int(time.time()) - lastop[userId] <= 300:
            return {"success": False, "msg": "You can only do one import each 5 minutes!"}
        else:
            del lastop[userId]

    dataUploadResult[userId] = ('', time.time())

    global threads
    if threads >= 8:
        return {"success": False, "msg": "The server is handling too many data import requests at this time... Please try again later!"}
    else:
        lastop[userId] = int(time.time())
        background_tasks.add_task(importWorkGate, userId, bookId, updateType, checkDuplicate, newlist)
    
    return {"success": True, "msg": "Working on it... <i class='fa fa-spinner fa-spin'></i>"}