# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import StreamingResponse, RedirectResponse, HTMLResponse, JSONResponse
import os, sys, datetime, time
import random, uuid
import json
import pandas as pd
import xlrd
import io

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Data API

lastop = {}
threads = 0
dlthreads = 0
dataUploadResult = {}
dataDownloadToken = {}
dataPreparation = {}

def clearOutdated():
    global dataUploadResult
    global dataPreparation
    
    t = list(dataUploadResult.keys())
    for userId in t:
        if not token in dataUploadResult.keys():
            continue
        if time.time() - dataUploadResult[userId][1] >= 120:
            del dataUploadResult[userId]
            
    t = list(dataDownloadToken.keys())
    for token in t:
        if not token in dataDownloadToken.keys():
            continue
        ts = dataDownloadToken[token][3]
        if time.time() - ts >= 300 and dataPreparation[token] != "Wait":
            del dataDownloadToken[token]
            del dataPreparation[token]
                
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

def prepareData(token):
    global dataDownloadToken
    global dataPreparation
    global dlthreads

    dlthreads += 1

    dataPreparation[token] = "Wait"

    d = dataDownloadToken[token]
    userId = d[0]
    exportType = d[1]
    bookId = d[2]
    
    StatusToStatusText = {-3: "Question bound to group", -2: "Added from website", -1: "File imported", 0: "None", 1: "Default", 2: "Tagged", 3: "Deleted"}

    conn = newconn()
    cur = conn.cursor()

    tempfile = f"/tmp/MyMemoTemp{userId}{int(time.time())}"

    if exportType == "xlsx":
        buf = io.BytesIO()
        df = pd.DataFrame()
        writer = pd.ExcelWriter(tempfile, engine='xlsxwriter')
        writer.book.filename = buf

        cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE userId = {userId}")
        t = cur.fetchall()
        d = []
        if bookId == 0:
            for tt in t:
                d.append((tt[1], tt[2], tt[3]))
        else:
            p = getBookData(userId, bookId)
            for tt in t:
                if tt[0] in p:
                    d.append((tt[1], tt[2], tt[3]))

        if len(d) == 0:
            df = df.append(pd.DataFrame([["","",""]], columns = ["Question", "Answer", "Status"]).astype(str))
        else:
            for dd in d:
                row = pd.DataFrame([[decode(dd[0]), decode(dd[1]), StatusToStatusText[dd[2]]]], columns = ["Question", "Answer", "Status"], index = [len(d)])
                df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Question List', index = False)
        writer.save()
        buf.seek(0)
        
        dataPreparation[token] = buf

        os.system(f"rm -f {tempfile}")
    
    else:
        buf = io.BytesIO()
        df = pd.DataFrame()
        writer = pd.ExcelWriter(tempfile, engine='xlsxwriter')
        writer.book.filename = buf

        cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], decode(dd[1]), decode(dd[2]), StatusToStatusText[dd[3]]]], columns = ["Question ID", "Question", "Answer", "Status"], index = [len(d)])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Question List', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT questionId, nextChallenge, lastChallenge FROM ChallengeData WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1], dd[2]]], columns = ["Question ID", "Next Challenge Timestamp", "Last Challenge Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Challenge Data', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT questionId, memorized, timestamp FROM ChallengeRecord WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1], dd[2]]], columns = ["Question ID", "Memorized (0/1)", "Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Challenge Record', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT questionId, questionUpdateId, updateTo, timestamp FROM StatusUpdate WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1], StatusToStatusText[dd[2]], dd[3]]], columns = ["Question ID", "Question Update ID", "Update To", "Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Question Status Update', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT bookId, name FROM Book WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], decode(dd[1])]], columns = ["Book ID", "Name"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Book List', index = False)
        df = pd.DataFrame()
        
        for dd in d:
            bookData = getBookData(userId, dd[0])
            for bd in bookData:
                row = pd.DataFrame([[dd[0], bd]], columns = ["Book ID", "Question ID"])
                df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Book Data', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT event, msg, timestamp FROM UserEvent WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], decode(dd[1]), dd[2]]], columns = ["Event", "Message", "Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'User Event', index = False)
        df = pd.DataFrame()

        writer.save()
        buf.seek(0)

        dataPreparation[token] = buf

        os.system(f"rm -f {tempfile}")
    
    dlthreads -= 1

@app.post("/api/data/export")
async def apiExportData(request: Request, background_tasks: BackgroundTasks):
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
    
    global dlthreads
    if dlthreads >= 8:
        return {"success": False, "msg": "The server is handling too many download requests at this time! Try again later..."}
    
    exportType = form["exportType"]
    bookId = int(form["bookId"])
    tk = str(uuid.uuid4())
    global dataDownloadToken
    dataDownloadToken[tk] = (userId, exportType, bookId, int(time.time()), tk)
    background_tasks.add_task(prepareData, tk)

    return {"success": True, "token": tk}

@app.post("/api/data/export/status")
async def apiExportStatus(request: Request):
    clearOutdated()
    ip = request.client.host
    conn = newconn()
    cur = conn.cursor()
    form = await request.form()

    token = form["token"]
    
    if not token in dataPreparation.keys():
        return {"success": False, "status": -1, "msg": "Invalid token!"}
    
    if dataPreparation[token] == "Wait":
        return {"success": True, "status": 0, "msg": "Please wait until the download is ready! <i class='fa fa-spinner fa-spin'></i>"}
    else:
        return {"success": True, "status": 1, "msg": "Download is ready!"}

def nginxException(status_code):
    return "/error?code=" + str(status_code)

@app.get("/download")
async def apiDownload(token: str, request: Request):
    clearOutdated()
    ip = request.client.host
    conn = newconn()
    cur = conn.cursor()
    if not token.replace("-","").isalnum():
        return RedirectResponse(nginxException(404))

    if not token in dataPreparation.keys():
        return "Invalid token!"
    
    buf = dataPreparation[token]
    if buf == "Wait":
        return "Download is still being prepared! Wait some seconds and refresh your page!"
    del dataPreparation[token]

    return StreamingResponse(buf, headers={"Content-Disposition": "attachment; filename=MyMemo_Export.xlsx", \
            "Content-Type": "application/octet-stream"})