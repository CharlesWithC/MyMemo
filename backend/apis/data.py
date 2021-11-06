# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort, send_file
import os, sys, datetime, time
import random, uuid
import json
import sqlite3
import pandas as pd
import xlrd
import threading
import io

from app import app, config
from functions import *
import sessions
import tempdb


##########
# Data API

@app.route("/api/data/import", methods = ['POST'])
def importData():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    # Do file check
    if 'file' not in request.files:
        return "Invalid import! E1: No file found"
    
    f = request.files['file']
    if f.filename == '':
        return "Invalid import! E2: Empty file name"

    if not f.filename.endswith(".xlsx"):
        return "Only .xlsx files are supported!"
    
    ts=int(time.time())

    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    newlist = None

    try:
        newlist = pd.read_excel(buf.getvalue(), engine = "openpyxl")
        if list(newlist.keys()).count("Question") != 1 or list(newlist.keys()).count("Answer")!=1:
            return "Invalid format! The columns must contain 'Question','Answer'!"
    except:
        return "Invalid format! The columns must contain 'Question','Answer'!"
    
    #####
    
    updateType = request.form["updateType"]
    yesno = {"yes": True, "no": False}
    checkDuplicate = request.form["checkDuplicate"]
    checkDuplicate = yesno[checkDuplicate]

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
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'question_limit'")
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

    if updateType  == "clear_overwrite":
        cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) > 0:
            ts = int(time.time())
            # for dd in d:
            #     cur.execute(f"INSERT INTO DeletedQuestionList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
            cur.execute(f"DELETE FROM BookData WHERE userId = {userId}")
            cur.execute(f"DELETE FROM QuestionList WHERE userId = {userId}")
    conn.commit()

    bookId = int(request.form["bookId"])
    bookList = []
    if bookId != 0:
        cur.execute(f"SELECT bookId FROM Book WHERE userId = {userId} AND bookId = {bookId}")
        if len(cur.fetchall()) == 0:
            bookId = 0
        else:
            cur.execute(f"SELECT questionId FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
            bookList = cur.fetchall()

    StatusTextToStatus = {"Default": 1, "Tagged": 2, "Removed": 3}

    for i in range(0, len(newlist)):
        question = str(newlist['Question'][i]).replace("\\n","\n")
        answer = str(newlist['Answer'][i]).replace("\\n","\n")

        if question in importDuplicate and updateType == "overwrite":
            wid = -1
            cur.execute(f"SELECT questionId FROM QuestionList WHERE userId = {userId} AND question = '{encode(question)}'")
            t = cur.fetchall()
            if len(t) > 0:
                wid = t[0][0]
            cur.execute(f"UPDATE QuestionList SET answer = '{encode(answer)}' WHERE questionId = {wid} AND userId = {userId}")
            if list(newlist.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
                status = StatusTextToStatus[newlist["Status"][i]]
                cur.execute(f"UPDATE QuestionList SET status = {status} WHERE questionId = {wid} AND userId = {userId}")
            if bookId != 0:
                if not (questionId,) in bookList:
                    cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")
                    bookList.append((questionId,))
                else:
                    cur.execute(f"UPDATE BookData SET bookId = {bookId} WHERE userId = {userId} AND questionId = {questionId}")
            continue

        status = -1
        questionId += 1
        updateQuestionStatus(userId, questionId, status)

        status = 1
        if list(newlist.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
            status = StatusTextToStatus[newlist["Status"][i]]
            updateQuestionStatus(userId, questionId, status)
        else:
            status = 1
            updateQuestionStatus(userId, questionId, status)
            
        cur.execute(f"INSERT INTO QuestionList VALUES ({userId},{questionId}, '{encode(question)}', '{encode(answer)}', {status})")
        cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{questionId}, 0, -1)")
        cur.execute(f"UPDATE IDInfo SET nextId = {questionId + 1} WHERE type = 2 AND userId = {userId}")
        
        if bookId != 0:
            cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, {questionId})")

    conn.commit()

    return "Data imported successfully!"

@app.route("/api/data/export", methods = ['POST'])
def exportData():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    exportType = request.form["exportType"]
    tk = str(uuid.uuid4())
    tempdb.cur.execute(f"INSERT INTO DataDownloadToken VALUES ({userId}, '{exportType}', {int(time.time())}, '{tk}')")
    tempdb.conn.commit()

    return json.dumps({"success": True, "token": tk})

queue = []
@app.route("/download", methods = ['GET'])
def download():
    token = request.args.get("token")
    if not token.replace("-").isalnum():
        abort(404)
    
    tempdb.cur.execute(f"SELECT * FROM DataDownloadToken WHERE token = '{token}'")
    d = tempdb.cur.fetchall()
    if len(d) == 0:
        abort(404)
    
    if config.max_concurrent_download != -1 and len(queue) > config.max_concurrent_download:
        abort(503)
    
    queue.append(token)
    
    userId = d[0][0]
    exportType = d[0][1]
    ts = d[0][2]
    tempdb.cur.execute(f"DELETE FROM DataDownloadToken WHERE token = '{token}'")
    tempdb.conn.commit()

    if int(time.time()) - ts > 1800: # 10 minutes
        abort(404)
    
    StatusToStatusText = {-3: "Question bound to group", -2: "Added from website", -1: "File imported", 0: "None", 1: "Default", 2: "Tagged", 3: "Removed"}

    cur = conn.cursor()

    if exportType == "xlsx":
        buf = io.BytesIO()
        df = pd.DataFrame()
        writer = pd.ExcelWriter('temp.xlsx', engine='xlsxwriter')
        writer.book.filename = buf

        cur.execute(f"SELECT question, answer, status FROM QuestionList WHERE userId = {userId}")
        d = cur.fetchall()

        if len(d) == 0:
            df = df.append(pd.DataFrame([["","",""]], columns = ["Question", "Answer", "Status"]).astype(str))
        else:
            for dd in d:
                row = pd.DataFrame([[decode(dd[0]), decode(dd[1]), StatusToStatusText[dd[2]]]], columns = ["Question", "Answer", "Status"], index = [len(d)])
                df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Question List', index = False)
        writer.save()
        buf.seek(0)

        queue.remove(token)

        return send_file(buf, as_attachment=True, attachment_filename='MyMemo_Export_QuestionList.xlsx', mimetype='application/octet-stream')
    
    else:
        buf = io.BytesIO()
        df = pd.DataFrame()
        writer = pd.ExcelWriter('temp.xlsx', engine='xlsxwriter')
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

        cur.execute(f"SELECT bookId, questionId FROM BookData WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1]]], columns = ["Book ID", "Question ID"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Book Data', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT event, timestamp FROM UserEvent WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1]]], columns = ["Event", "Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'User Event', index = False)
        df = pd.DataFrame()

        writer.save()
        buf.seek(0)

        queue.remove(token)

        return send_file(buf, as_attachment=True, attachment_filename='MyMemo_Export_AllData.xlsx', mimetype='application/octet-stream')

def ClearOutdatedDLToken():
    while 1:
        tempdb.cur.execute(f"DELETE FROM DataDownloadToken WHERE ts <= {int(time.time()) - 1800}")
        tempdb.conn.commit()
        time.sleep(600)

threading.Thread(target=ClearOutdatedDLToken).start()