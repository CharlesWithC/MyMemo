# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort, send_file
import os, sys, datetime, time
import random, uuid
import json
import pandas as pd
import xlrd
import threading
import io

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Data API

lastop = {}
threads = 0

def importWork(userId, bookId, updateType, checkDuplicate, newlist):
    global threads
    threads += 1
        
    conn = newconn()
    cur = conn.cursor()

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
        cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) > 0:
            ts = int(time.time())
            cur.execute(f"DELETE FROM BookData WHERE userId = {userId}")
            cur.execute(f"DELETE FROM QuestionList WHERE userId = {userId}")
        
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
                removeBookData(uid, p[0][0], qid)
            cur.execute(f"DELETE FROM GroupQuestion WHERE groupId = {groupId}")
            cur.execute(f"DELETE FROM GroupSync WHERE groupId = {groupId}")
    
    conn.commit()

    StatusTextToStatus = {"Default": 1, "Tagged": 2, "Removed": 3}

    groupMember = None
    if groupId != -1:
        cur.execute(f"SELECT userId, bookId FROM GroupMember WHERE groupId = {groupId}")
        groupMember = cur.fetchall()
    
    cur.execute(f"SELECT question, questionId FROM QuestionList WHERE userId = {userId}")
    qlist = cur.fetchall()

    progress = 0
    for i in range(0, len(newlist)):
        question = str(newlist['Question'][i]).replace("\\n","\n")
        answer = str(newlist['Answer'][i]).replace("\\n","\n")
        if int(i / len(newlist) * 100) > progress:
            progress = int(i / len(newlist) * 100)
            cur.execute(f"UPDATE DataUploadResult SET result = '{encode(f'Progress{progress}')}' WHERE userId = {userId}")
            conn.commit()

        if question in importDuplicate and updateType == "overwrite":
            wid = -1
            for q in qlist:
                if q[0] == encode(question):
                    wid = q[1]
            
            if wid != -1:
                if len(encode(answer)) >= 40960:
                    return "Answer too long: " + answer

                cur.execute(f"UPDATE QuestionList SET answer = '{encode(answer)}' WHERE questionId = {wid} AND userId = {userId}")
                if list(newlist.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
                    status = StatusTextToStatus[newlist["Status"][i]]
                    cur.execute(f"UPDATE QuestionList SET status = {status} WHERE questionId = {wid} AND userId = {userId}")
                if bookId != 0 and not questionId in bookList:
                    appendBookData(userId, bookId, questionId)
                    bookList.append(questionId)
                    
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
            
        if len(encode(question)) >= 40960:
            return "Question too long:" + question
        if len(encode(answer)) >= 40960:
            return "Answer too long:" + answer
        
        cur.execute(f"INSERT INTO QuestionList VALUES ({userId},{questionId}, '{encode(question)}', '{encode(answer)}', {status}, 0)")
        cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{questionId}, 0, -1)")
        cur.execute(f"UPDATE IDInfo SET nextId = {questionId + 1} WHERE type = 2 AND userId = {userId}")
        
        if bookId != 0:
            appendBookData(userId, bookId, questionId)

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
                    appendBookData(uid, wbid, wid)
                    cur.execute(f"INSERT INTO ChallengeData VALUES ({uid},{wid},0,-1)")
                    cur.execute(f"INSERT INTO GroupSync VALUES ({groupId}, {uid}, {wid}, {gquestionId})")
                    updateQuestionStatus(uid, wid, -3) # -3 is group question
                    updateQuestionStatus(uid, wid, 1) # 1 is default status

    conn.commit()
    threads -= 1
    return "Success!"

def clearResult(userId, deleteNow = False, deleteAfter = 30):
    if not deleteNow:
        time.sleep(deleteAfter)
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM DataUploadResult WHERE userId = {userId}")
    conn.commit()

def importWorkGate(userId, bookId, updateType, checkDuplicate, newlist):
    conn = newconn()
    cur = conn.cursor()

    res = ""
    try:
        res = importWork(userId, bookId, updateType, checkDuplicate, newlist)
    except:
        import traceback
        traceback.print_exc()
        res = "Failed"
        global lastop
        if userId in lastop.keys():
            del lastop[userId]
    
    conn = newconn()
    cur = conn.cursor()
    
    for _ in range(3):
        try:
            cur.execute(f"SELECT * FROM DataUploadResult WHERE userId = {userId}")
            if len(cur.fetchall()) > 0:
                cur.execute(f"UPDATE DataUploadResult SET result = '{encode(res)}' WHERE userId = {userId}")
            else:
                cur.execute(f"INSERT INTO DataUploadResult VALUES ({userId}, '{encode(res)}')")
            conn.commit()
            break
        except:
            import traceback
            traceback.print_exc()
            conn = newconn()
            cur = conn.cursor()
    
    threading.Thread(target=clearResult,args=(userId,)).start()

@app.route("/api/data/import", methods = ['POST'])
def importData():
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    if "getResult" in request.form.keys():
        cur.execute(f"SELECT result FROM DataUploadResult WHERE userId = {userId}")
        t = cur.fetchall()
        if len(t) > 0:
            if t[0][0] != '':
                if decode(t[0][0]) == "Failed":
                    threading.Thread(target=clearResult,args=(userId,True,)).start()
                    return json.dumps({"success": 0, "msg": decode(t[0][0])})
                elif decode(t[0][0]).startswith("Progress"):
                    progress = decode(t[0][0]).replace("Progress","")
                    return json.dumps({"success": 1, "msg": f"Still working on it ... {progress}% Finished"})
                else:
                    threading.Thread(target=clearResult,args=(userId,True,)).start()
                    return json.dumps({"success": 2, "msg": decode(t[0][0])})
            else:
                return json.dumps({"success": 1, "msg": "Still working on it... <i class='fa fa-spinner fa-spin'></i>"})
        return json.dumps({"success": 0, "msg": "Upload result has been cleared!"})

    cur.execute(f"SELECT result FROM DataUploadResult WHERE userId = {userId}")
    t = cur.fetchall()
    if len(t) > 0:
        return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>Another upload task is running!</p>"

    # Do file check
    if 'file' not in request.files:
        return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>Invalid import! E1: No file found</p>"
    
    f = request.files['file']
    if f.filename == '':
        return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>Invalid import! E2: Empty file name</p>"

    if not f.filename.endswith(".xlsx"):
        return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>Only .xlsx files are supported!</p>"
    
    ts=int(time.time())

    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    newlist = None

    try:
        newlist = pd.read_excel(buf.getvalue(), engine = "openpyxl")
        if list(newlist.keys()).count("Question") != 1 or list(newlist.keys()).count("Answer")!=1:
            return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>Invalid format! The columns must contain 'Question','Answer'!</p>"
    except:
        return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>Invalid format! The columns must contain 'Question','Answer'!</p>"
    
    updateType = request.form["updateType"]
    yesno = {"yes": True, "no": False}
    checkDuplicate = request.form["checkDuplicate"]
    checkDuplicate = yesno[checkDuplicate]

    bookId = int(request.form["bookId"])

    cur.execute(f"INSERT INTO DataUploadResult VALUES ({userId}, '')")
    conn.commit()

    global lastop
    if userId in lastop.keys():
        if int(time.time()) - lastop[userId] <= 300:
            return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>You can only do one import each 5 minutes!</p>"
        else:
            del lastop[userId]

    global threads
    if threads >= 8:
        return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><link href='/css/main.css' rel='stylesheet'><p>The server is handling too many data import requests at this time... Please try again later!</p>"
    else:
        lastop[userId] = int(time.time())
        threading.Thread(target=importWorkGate,args=(userId, bookId, updateType, checkDuplicate, newlist, )).start()
        threading.Thread(target=clearResult,args=(userId,False,300,)).start()

    return "<script src='https://cdn.charles14.xyz/js/jquery-3.6.0.min.js'></script><script src='/js/general.js'></script><script>GetUploadResult()</script>\
        <link href='/css/all.min.css' rel='stylesheet'><link href='/css/main.css' rel='stylesheet'>\
            <p id='result'>Working on it... <i class='fa fa-spinner fa-spin'></i></p>"

@app.route("/api/data/export", methods = ['POST'])
def exportData():
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    exportType = request.form["exportType"]
    tk = str(uuid.uuid4())
    cur.execute(f"INSERT INTO DataDownloadToken VALUES ({userId}, '{exportType}', {int(time.time())}, '{tk}')")
    conn.commit()

    return json.dumps({"success": True, "token": tk})

queue = []
@app.route("/download", methods = ['GET'])
def download():
    conn = newconn()
    cur = conn.cursor()
    token = request.args.get("token")
    if not token.replace("-").isalnum():
        abort(404)
    
    cur.execute(f"SELECT * FROM DataDownloadToken WHERE token = '{token}'")
    d = cur.fetchall()
    if len(d) == 0:
        abort(404)
    
    if config.max_concurrent_download != -1 and len(queue) > config.max_concurrent_download:
        abort(503)
    
    queue.append(token)
    
    userId = d[0][0]
    exportType = d[0][1]
    ts = d[0][2]
    cur.execute(f"DELETE FROM DataDownloadToken WHERE token = '{token}'")
    conn.commit()

    if int(time.time()) - ts > 1800: # 10 minutes
        abort(404)
    
    StatusToStatusText = {-3: "Question bound to group", -2: "Added from website", -1: "File imported", 0: "None", 1: "Default", 2: "Tagged", 3: "Removed"}

    conn = newconn()
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
        
        for dd in d:
            bookData = getBookData(userId, dd[0])
            for bd in bookData:
                row = pd.DataFrame([[dd[0], bd]], columns = ["Book ID", "Question ID"])
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
        conn = newconn()
        cur = conn.cursor()
        cur.execute(f"DELETE FROM DataDownloadToken WHERE ts <= {int(time.time()) - 1800}")
        conn.commit()
        time.sleep(600)

threading.Thread(target=ClearOutdatedDLToken).start()