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
        if list(newlist.keys()).count("Word") != 1 or list(newlist.keys()).count("Translation")!=1:
            return "Invalid format! The columns must contain 'Word','Translation'!"
    except:
        return "Invalid format! The columns must contain 'Word','Translation'!"
    
    #####
    
    updateType = request.form["updateType"]
    yesno = {"yes": True, "no": False}
    checkDuplicate = request.form["checkDuplicate"]
    checkDuplicate = yesno[checkDuplicate]

    importDuplicate = []
    cur.execute(f"SELECT word FROM WordList WHERE userId = {userId}")
    wordList = cur.fetchall()
    for i in range(0, len(newlist)):
        if (encode(str(newlist["Word"][i])),) in wordList:
            importDuplicate.append(str(newlist["Word"][i]))

    if checkDuplicate and updateType == "append":
        if len(importDuplicate) != 0:
            return f"Upload rejected due to duplicated words: {' ; '.join(importDuplicate)}"

    
    max_allow = config.max_word_per_user_allowed
    cur.execute(f"SELECT value FROM Previlege WHERE userId = {userId} AND item = 'word_limit'")
    pr = cur.fetchall()
    if len(pr) != 0:
        max_allow = pr[0][0]
    cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) != 0 and max_allow != -1 and d[0][0] + len(newlist) >= max_allow:
        return f"You have reached your limit of maximum added words {max_allow}. Remove some old words or contact administrator for help."

    wordId = 1
    cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 2 AND userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0:
        cur.execute(f"INSERT INTO IDInfo VALUES (2, {userId}, 2)")
    else:
        wordId = d[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {wordId + 1} WHERE type = 2 AND userId = {userId}")

    if updateType  == "clear_overwrite":
        cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId}")
        d = cur.fetchall()
        if len(d) > 0:
            ts = int(time.time())
            # for dd in d:
            #     cur.execute(f"INSERT INTO DeletedWordList VALUES ({userId},{dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {userId}")
            cur.execute(f"DELETE FROM WordList WHERE userId = {userId}")
    conn.commit()

    wordBookId = int(request.form["wordBookId"])
    wordBookList = []
    if wordBookId != 0:
        cur.execute(f"SELECT wordBookId FROM WordBook WHERE userId = {userId} AND wordBookId = {wordBookId}")
        if len(cur.fetchall()) == 0:
            wordBookId = 0
        else:
            cur.execute(f"SELECT wordId FROM WordBookData WHERE userId = {userId} AND wordBookId = {wordBookId}")
            wordBookList = cur.fetchall()

    StatusTextToStatus = {"Default": 1, "Tagged": 2, "Removed": 3}

    for i in range(0, len(newlist)):
        word = str(newlist['Word'][i]).replace("\\n","\n")
        translation = str(newlist['Translation'][i]).replace("\\n","\n")

        if word in importDuplicate and updateType == "overwrite":
            cur.execute(f"SELECT wordId FROM WordList WHERE userId = {userId} AND word = '{encode(word)}'")
            wid = cur.fetchall()[0][0] # do not use wordId as variable name or it will cause conflict
            cur.execute(f"UPDATE WordList SET translation = '{encode(translation)}' WHERE wordId = {wid} AND userId = {userId}")
            if list(newlist.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
                status = StatusTextToStatus[newlist["Status"][i]]
                cur.execute(f"UPDATE WordList SET status = {status} WHERE wordId = {wid} AND userId = {userId}")
            if wordBookId != 0:
                if not (wordId,) in wordBookList:
                    cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")
                    wordBookList.append((wordId,))
                else:
                    cur.execute(f"UPDATE WordBookData SET wordBookId = {wordBookId} WHERE userId = {userId} AND wordId = {wordId}")
            continue

        status = -1
        wordId += 1
        updateWordStatus(userId, wordId, status)

        status = 1
        if list(newlist.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
            status = StatusTextToStatus[newlist["Status"][i]]
            updateWordStatus(userId, wordId, status)
        else:
            status = 1
            updateWordStatus(userId, wordId, status)
            
        cur.execute(f"INSERT INTO WordList VALUES ({userId},{wordId}, '{encode(word)}', '{encode(translation)}', {status})")
        cur.execute(f"INSERT INTO ChallengeData VALUES ({userId},{wordId}, 0, -1)")
        cur.execute(f"UPDATE IDInfo SET nextId = {wordId + 1} WHERE type = 2 AND userId = {userId}")
        
        if wordBookId != 0:
            cur.execute(f"INSERT INTO WordBookData VALUES ({userId}, {wordBookId}, {wordId})")

    conn.commit()

    return "Data imported successfully!"

dltoken = {}
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
    dltoken[tk] = (userId, exportType, int(time.time()))

    return json.dumps({"success": True, "token": tk})

queue = []
@app.route("/download", methods = ['GET'])
def download():
    global dltoken
    token = request.args.get("token")
    if not token in dltoken.keys():
        abort(404)
    
    if config.max_concurrent_download != -1 and len(queue) > config.max_concurrent_download:
        abort(503)
    
    queue.append(token)
    
    userId = dltoken[token][0]
    exportType = dltoken[token][1]
    ts = dltoken[token][2]
    del dltoken[token]

    if int(time.time()) - ts > 1800: # 10 minutes
        abort(404)
    
    StatusToStatusText = {-3: "Word bound to group", -2: "Added from website", -1: "File imported", 0: "None", 1: "Default", 2: "Tagged", 3: "Removed"}

    cur = conn.cursor()

    if exportType == "xlsx":
        buf = io.BytesIO()
        df = pd.DataFrame()
        writer = pd.ExcelWriter('temp.xlsx', engine='xlsxwriter')
        writer.book.filename = buf

        cur.execute(f"SELECT word, translation, status FROM WordList WHERE userId = {userId}")
        d = cur.fetchall()

        if len(d) == 0:
            df = df.append(pd.DataFrame([["","",""]], columns = ["Word", "Translation", "Status"]).astype(str))
        else:
            for dd in d:
                row = pd.DataFrame([[decode(dd[0]), decode(dd[1]), StatusToStatusText[dd[2]]]], columns = ["Word", "Translation", "Status"], index = [len(d)])
                df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Word List', index = False)
        writer.save()
        buf.seek(0)

        queue.remove(token)

        return send_file(buf, as_attachment=True, attachment_filename='WordMemo_Export_WordList.xlsx', mimetype='application/octet-stream')
    
    else:
        buf = io.BytesIO()
        df = pd.DataFrame()
        writer = pd.ExcelWriter('temp.xlsx', engine='xlsxwriter')
        writer.book.filename = buf

        cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], decode(dd[1]), decode(dd[2]), StatusToStatusText[dd[3]]]], columns = ["Word ID", "Word", "Translation", "Status"], index = [len(d)])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Word List', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT wordId, nextChallenge, lastChallenge FROM ChallengeData WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1], dd[2]]], columns = ["Word ID", "Next Challenge Timestamp", "Last Challenge Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Challenge Data', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT wordId, memorized, timestamp FROM ChallengeRecord WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1], dd[2]]], columns = ["Word ID", "Memorized (0/1)", "Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Challenge Record', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT wordId, wordUpdateId, updateTo, timestamp FROM StatusUpdate WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1], StatusToStatusText[dd[2]], dd[3]]], columns = ["Word ID", "Word Update ID", "Update To", "Timestamp"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Word Status Update', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT wordBookId, name FROM WordBook WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], decode(dd[1])]], columns = ["Word Book ID", "Name"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Word Book List', index = False)
        df = pd.DataFrame()

        cur.execute(f"SELECT wordBookId, wordId FROM WordBookData WHERE userId = {userId}")
        d = cur.fetchall()
        for dd in d:
            row = pd.DataFrame([[dd[0], dd[1]]], columns = ["Word Book ID", "Word ID"])
            df = df.append(row.astype(str))
        df.to_excel(writer, sheet_name = 'Word Book Data', index = False)
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

        return send_file(buf, as_attachment=True, attachment_filename='WordMemo_Export_AllData.xlsx', mimetype='application/octet-stream')

def ClearOutdatedDLToken():
    global dltoken
    while 1:
        for token in dltoken.keys():
            if int(time.time()) - dltoken[token][2] > 1800:
                del dltoken[token]
        time.sleep(600)

threading.Thread(target=ClearOutdatedDLToken).start()