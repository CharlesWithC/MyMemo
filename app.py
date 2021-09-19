# Author: @Charles-1414

from flask import Flask, render_template, request, abort, send_file
import os, random, json, time, base64, hashlib, threading, math
import urllib.parse
import sqlite3
import pandas as pd

StatusTextToStatus = {"Default": 1, "Tagged": 2, "Removed": 3}
StatusToStatusText = {1: "Default", 2: "Tagged", 3: "Removed"}
wordCnt = 0

db_exists = os.path.exists("database.db")
conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()
if not db_exists:
    cur.execute(f"CREATE TABLE WordList (wordId INT, word VARCHAR(1024), definition VARCHAR(1024), status INT)")
    # wordId is unique for each word, when the word is removed, its wordId will refer to null
    # word and definition are encoded with base64 to prevent datalose
    # status is a status code while 1 refers to Default, 2 refers to Tagged and 3 refers to removed

    cur.execute(f"CREATE TABLE DeletedWordList (wordId INT, word VARCHAR(1024), definition VARCHAR(1024), status INT, deleteTimestamp INT)")

    cur.execute(f"CREATE TABLE StatusUpdate (wordId INT, wordUpdateId INT, updateTo INT, timestamp INT)")
    # wordUpdateId is the Id for the specific word
    # updateTo is the status the word is updated to
    # NOTE: When a new word is added, there should be a StatusUpdate record, with wordUpdateId = 0 and updateTo = 0
    
    cur.execute(f"CREATE TABLE UserInfo (password VARCHAR(256))")
    cur.execute(f"INSERT INTO UserInfo VALUES ('49dc52e6bf2abe5ef6e2bb5b0f1ee2d765b922ae6cc8b95d39dc06c21c848f8c')")

    conn.commit()

def insert_newlines(string, every=16):
    return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

def encode(s):
    return base64.b64encode(s.encode()).decode()

def decode(s):
    return base64.b64decode(s.encode()).decode()

def getWordCount():
    cur.execute(f"SELECT COUNT(*) FROM WordList")
    return cur.fetchall()[0][0]

def updateWordStatus(wordId, status):
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE wordId = {wordId}")
    d = cur.fetchall()
    wordUpdateId = 0
    if len(d) != 0:
        wordUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({wordId},{wordUpdateId},{status},{int(time.time())})")


app=Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getWord")
def getWord():
    wordId = int(request.args["wordId"])
    splitLine = int(request.args["splitLine"])
    
    cur.execute(f"SELECT word, definition, status FROM WordList WHERE wordId = {wordId}")
    d = cur.fetchall()

    if len(d) == 0:
        abort(404)
    
    (word, definition, status) = d[0]
    word = decode(word)
    definition = decode(definition)
    definition = insert_newlines(definition, splitLine)

    return json.dumps({"wordId": wordId, "word":word, "definition": definition, "status": status})

@app.route("/getWordId")
def getWordID():
    word = urllib.parse.unquote(request.args["word"])
    cur.execute(f"SELECT wordId FROM WordList WHERE word = '{encode(word)}'")
    d = cur.fetchall()
    wordId = -1
    if len(d) != 0:
        wordId = d[0][0]
        # If there are multiple records, then return the first one
        # NOTE: The user should be warned when they try to insert multiple records with the same word

    return json.dumps({"wordId" : wordId})

@app.route("/getNext")
def getNext():
    wordId = -1

    op = {-1: "<", 1: ">"}
    order = {-1: "DESC", 1: "ASC"}
    moveType = int(request.args["moveType"]) # -1: previous, 1: next, 0: random
    if moveType in [-1,1]:
        op = op[moveType]
        order = order[moveType]

    current = -1
    if moveType in [-1, 1]:
        current = int(request.args["wordId"])

    statusRequirement = {1: "status = 1 OR status = 2", 2: "status = 2", 3: "status = 3"}
    status = int(request.args["status"])
    statusRequirement = statusRequirement[status]

    if moveType in [-1,1]:
        cur.execute(f"SELECT wordId, word, definition, status FROM WordList WHERE wordId{op}{current} AND {statusRequirement} ORDER BY wordId {order} LIMIT 1")
        d = cur.fetchall()
        if len(d) == 0: # no matching results, then find result from first / end
            cur.execute(f"SELECT wordId, word, definition, status FROM WordList WHERE {statusRequirement} ORDER BY wordId {order} LIMIT 1")
            d = cur.fetchall()

    elif moveType == 0:
        cur.execute(f"SELECT wordId, word, definition, status FROM WordList WHERE {statusRequirement} ORDER BY RANDOM() LIMIT 1")
        d = cur.fetchall()

    if len(d) == 0:
        abort(404)

    (wordId, word, definition, status) = d[0]
    word = decode(word)
    definition = decode(definition)

    splitLine = int(request.args["splitLine"])
    definition = insert_newlines(definition, splitLine)

    return json.dumps({"wordId": wordId, "word": word, "definition": definition, "status": status})

@app.route("/getWordCount")
def getCount():
    return json.dumps({"count": str(getWordCount())})

@app.route("/updateStatus")
def updateStatus():
    wordId = int(request.args["wordId"])
    status = int(request.args["status"])

    cur.execute(f"SELECT word FROM WordList WHERE wordId = {wordId}")
    if len(cur.fetchall()) == 0:
        return json.dumps({"succeed": False, "msg": "Word not found!"})

    cur.execute(f"UPDATE WordList SET status = {status} WHERE wordId = {wordId}")

    updateWordStatus(wordId, status)

    conn.commit()

    return json.dumps({"succeed": True})

@app.route("/changePassword", methods=['GET','POST'])
def changePassword():
    if request.method=='POST':
        oldpwd = request.form["oldpwd"]
        newpwd = request.form["newpwd"]
        cfmpwd = request.form["cfmpwd"]
        
        cur.execute(f"SELECT password FROM UserInfo")
        pwd = cur.fetchall()[0][0]
        oldhashed = hashlib.sha256(hashlib.sha256(oldpwd.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
        if oldhashed != pwd:
            return render_template("changepwd.html", MESSAGE = "Incorrect old password!")
        if newpwd != cfmpwd:
            return render_template("changepwd.html", MESSAGE = "New password and confirm password mismatch!")

        newhashed = hashlib.sha256(hashlib.sha256(newpwd.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
        cur.execute(f"UPDATE UserInfo SET password = '{newhashed}'")
        conn.commit()

        return render_template("changepwd.html", MESSAGE = "Password updated!")
        
    else:
        return render_template("changepwd.html", MESSAGE = "")

@app.route("/importData", methods = ['GET', 'POST'])
def importData():
    if request.method == 'POST':
        cur.execute(f"SELECT password FROM UserInfo")
        pwd = cur.fetchall()[0][0]

        password = request.form["password"]
        hashed = hashlib.sha256(hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
        if hashed != pwd:
            return render_template("import.html", MESSAGE = "Invalid password!")

        # Do file check
        if 'file' not in request.files:
            return render_template("import.html", MESSAGE = "Invalid import! E1: No file found")
        
        f = request.files['file']
        if f.filename == '':
            return render_template("import.html", MESSAGE = "Invalid import! E2: Empty file name")

        if not f.filename.endswith(".xlsx"):
            return render_template("import.html", MESSAGE = "Only .xlsx files are supported!")
        
        ts=int(time.time())
        f.save(f"/tmp/data{ts}.xlsx")

        try:
            uploaded = pd.read_excel(f"/tmp/data{ts}.xlsx")
            if list(uploaded.keys()).count("Word") != 1 or list(uploaded.keys()).count("Definition")!=1:
                os.system(f"rm -f /tmp/data{ts}.xlsx")
                return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Definition'!")
        except:
            os.system(f"rm -f /tmp/data{ts}.xlsx")
            return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Definition'!")
        
        #####
        
        updateType = request.form["updateType"]
        yesno = {"yes": True, "no": False}
        checkDuplicate = request.form["checkDuplicate"]
        checkDuplicate = yesno[checkDuplicate]

        newlist = pd.read_excel(f"/tmp/data{ts}.xlsx")
        duplicate = []
        if checkDuplicate and updateType != "overwrite":
            cur.execute(f"SELECT word FROM WordList")
            wordList = cur.fetchall()
            for i in range(0, len(newlist)):
                if (encode(newlist["Word"][i]),) in wordList:
                    duplicate.append(newlist["Word"][i])

            if len(duplicate) != 0:
                return render_template("import.html", MESSAGE = f"Upload rejected due to duplicated words: {' ; '.join(duplicate)}")

        wordId = 0

        if updateType == "append":
            cur.execute(f"SELECT wordId FROM WordList ORDER BY wordId DESC LIMIT 1")
            d = cur.fetchall()
            if len(d) != 0:
                wordId = d[0][0]
                
        elif updateType  == "overwrite":
            cur.execute(f"SELECT * FROM WordList")
            d = cur.fetchall()
            ts = int(time.time())
            for dd in d:
                cur.execute(f"INSERT INTO DeletedWordList VALUES ({dd[0]}, '{dd[1]}', '{dd[2]}', {dd[3]}, {ts})")
            cur.execute(f"DELETE FROM WordList")
            conn.commit()

        for i in range(0, len(newlist)):
            status = 0
            wordId += 1
            updateWordStatus(wordId, status)

            status = 1
            if list(uploaded.keys()).count("Status") == 1 and newlist["Status"][i] in ["Default", "Tagged", "Removed"]:
                status = StatusTextToStatus[newlist["Status"][i]]
            updateWordStatus(wordId, status)
            
            if type(newlist['Word'][i]) != str:
                newlist['Word'][i] = "[Unknown word]"
            if type(newlist['Definition'][i]) != str:
                newlist['Definition'][i] = "[Unknown definition]"

            cur.execute(f"INSERT INTO WordList VALUES ({wordId}, '{encode(newlist['Word'][i])}', '{encode(newlist['Definition'][i])}', {status})")
            
        conn.commit()

        os.system(f"rm -f /tmp/data{ts}.xlsx")

        return render_template("import.html", MESSAGE = "Data imported successfully!")

    else:
        return render_template("import.html", MESSAGE = "")

@app.route("/exportData", methods = ['GET', 'POST'])
def exportData():
    if request.method == "POST":
        cur.execute(f"SELECT password FROM UserInfo")
        pwd = cur.fetchall()[0][0]

        password = request.form["password"]
        hashed = hashlib.sha256(hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
        if hashed != pwd:
            return render_template("export.html", MESSAGE = "Invalid password!")
        
        exportType = request.form["exportType"]

        if exportType == "xlsx":
            cur.execute(f"SELECT word, definition, status FROM WordList")
            d = cur.fetchall()
            if len(d) == 0:
                return render_template("export.html", MESSAGE = "Empty word list!")
            
            xlsx = pd.DataFrame()
            for dd in d:
                word = pd.DataFrame([[decode(dd[0]), decode(dd[1]), StatusToStatusText[dd[2]]]],columns=["Word","Definition","Status"],index=[len(d)])
                xlsx = xlsx.append(word)

            xlsx.to_excel('/tmp/export.xlsx', sheet_name='Data', index=False)

            return send_file("/tmp/export.xlsx", as_attachment=True)
        
        else:
            os.system("cp ./database.db /tmp/export.db")
            export_conn = sqlite3.connect("/tmp/export.db")
            export_cur = export_conn.cursor()
            export_cur.execute(f"DROP TABLE UserInfo")
            export_conn.commit()

            return send_file("/tmp/export.db", as_attachment=True)


    else:
        return render_template("export.html", MESSAGE = "")

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run("127.0.0.1",8888)