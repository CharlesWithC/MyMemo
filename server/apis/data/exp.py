# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, RedirectResponse
import os, sys, time
import uuid
import pandas as pd
import io

from app import app, config
from db import newconn
from functions import *

##########
# Data API
# Export

threads = 0
dataDownloadToken = {}
dataPreparation = {}

def clearOutdated():
    global dataDownloadToken
    global dataPreparation
            
    t = list(dataDownloadToken.keys())
    for token in t:
        if not token in dataDownloadToken.keys():
            continue
        ts = dataDownloadToken[token][3]
        if time.time() - ts >= 300 and dataPreparation[token] != "Wait":
            del dataDownloadToken[token]
            del dataPreparation[token]

def prepareData(token):
    global dataDownloadToken
    global dataPreparation
    global threads

    threads += 1

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
    
    threads -= 1

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
    
    global threads
    if threads >= 8:
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