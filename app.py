# Author: @Charles-1414

from flask import Flask, render_template, request, abort, send_file
import os, random, json, datetime, time, base64, hashlib
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
    cur.execute(f"CREATE TABLE WordList (wordId INT, word VARCHAR(1024), translation VARCHAR(1024), status INT)")
    # wordId is unique for each word, when the word is removed, its wordId will refer to null
    # word and translation are encoded with base64 to prevent datalose
    # status is a status code while 1 refers to Default, 2 refers to Tagged and 3 refers to removed

    cur.execute(f"CREATE TABLE ChallengeData (wordId INT, nextChallenge INT, lastChallenge INT)")
    # Challenge Data is a table that tells when to display the word next time
    # nextChallenge and lastChallenge are both timestamps
    # When a new word is added, there should be a record of it with nextChallenge = 0, lastChallenge = -1
    # When the user says that he/she memorized the word, then nextChallenge will be extended to a longer time based on forgetting curve
    # When the user says that he/she forgot the word, then nextChallenge will be set to 1 hour later

    # In challenge mode, the words to display contains all the words in the wordlist
    # The percentage of showing a word is:
    # 35%: Words that are tagged
    # 30%: NextChallenge != 0 && NextChallenge <= int(time.time())
    # 30%: NextChallenge == 0
    # 5%: Words that are deleted (to make sure the user still remember it)

    cur.execute(f"CREATE TABLE ChallengeRecord (wordId INT, memorized INT, timestamp INT)")
    # This is the record of historical challenges

    cur.execute(f"CREATE TABLE DeletedWordList (wordId INT, word VARCHAR(1024), translation VARCHAR(1024), status INT, deleteTimestamp INT)")
    # This is the list of all permanently deleted words (which will never be shown on user side)

    cur.execute(f"CREATE TABLE StatusUpdate (wordId INT, wordUpdateId INT, updateTo INT, timestamp INT)")
    # wordUpdateId is the Id for the specific word
    # updateTo is the status the word is updated to
    # NOTE: When a new word is added, there should be a StatusUpdate record, with wordUpdateId = 0 and updateTo = 0
    
    cur.execute(f"CREATE TABLE UserInfo (password VARCHAR(256))")
    cur.execute(f"INSERT INTO UserInfo VALUES ('49dc52e6bf2abe5ef6e2bb5b0f1ee2d765b922ae6cc8b95d39dc06c21c848f8c')")
    # Default password is 123456

    conn.commit()

def insert_newlines(string, every=16):
    pos = 0
    for i in range(0, len(string)):
        if string[i] == '\n':
            pos = i
        if i > pos + every:
            string = string[:i] + '\n' + string[i:]
            pos = i
    return string

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
    
    cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId}")
    d = cur.fetchall()

    if len(d) == 0:
        abort(404)
    
    (word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)
    translation = insert_newlines(translation, splitLine)

    return json.dumps({"wordId": wordId, "word":word, "translation": translation, "status": status})

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

@app.route("/getWordStat")
def getWordStat():
    wordId = int(request.args["wordId"])
    cur.execute(f"SELECT word FROM WordList WHERE wordId = {wordId}")
    d = cur.fetchall()
    if len(d) == 0:
        abort(404)
    word = decode(d[0][0])
    
    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE wordId = {wordId} AND updateTo <= 0")
    d = cur.fetchall()[0]
    astatus = d[0] # how it is added
    ats = d[1] # addition timestamp

    cur.execute(f"SELECT updateTo, timestamp FROM StatusUpdate WHERE wordId = {wordId}")
    d = cur.fetchall()

    status = 1

    tagcnt = 0
    lsttag = 0
    untagcnt = 0
    lstuntag = 0

    delcnt = 0
    lstdel = 0
    undelcnt = 0
    lstundel = 0

    for i in range(2, len(d)):
        if status == 1 and d[i][0] == 2:
            tagcnt += 1
            lsttag = d[i][1]
        elif status == 2 and d[i][0] == 1:
            untagcnt += 1
            lstuntag = d[i][1]
        elif status == 1 and d[i][0] == 3:
            delcnt += 1
            lstdel = d[i][1]
        elif status == 3 and d[i][0] == 1:
            undelcnt += 1
            lstundel = d[i][1]
        status = d[i][0]
    
    cur.execute(f"SELECT nextChallenge, lastChallenge FROM ChallengeData WHERE wordId = {wordId}")
    d = cur.fetchall()[0]
    nxt = d[0]
    lst = d[1]

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE wordId = {wordId}")
    d = cur.fetchall()
    appeared = len(d)
    mem = 0
    lstmem = 0
    fgt = 0
    lstfgt = 0
    for dd in d:
        if dd[0] == 1:
            mem += 1
            lstmem = dd[1]
        elif dd[0] == 0:
            fgt += 1
            lstfgt = dd[1]
    lst30d = 0
    lst30dmem = 0
    lst7d = 0
    lst7dmem = 0
    lst1d = 0
    lst1dmem = 0
    for dd in d:
        if (time.time() - dd[1]) <= 86400*30:
            lst30d += 1
            lst30dmem += dd[0]
        if (time.time() - dd[1]) <= 86400*7:
            lst7d += 1
            lst7dmem += dd[0]
        if (time.time() - dd[1]) <= 86400:
            lst1d += 1
            lst1dmem += dd[0]
    
    def ts2dt(ts):
        return datetime.datetime.fromtimestamp(ts)

    res = f"About {word}\n"

    if astatus == 0:
        res += f"Added at {ts2dt(ats)} with .xlsx importer.\n"    
    elif astatus == -1:
        res += f"Added at {ts2dt(ats)} on website.\n"    

    if tagcnt > 0:
        res += f"Tagged for {tagcnt} times\n(Last time: {ts2dt(lsttag)}),\n"
    else:
        res += f"Never tagged,\n"
    if delcnt > 0:
        res += f"Deleted for {delcnt} times\n(Last time: {ts2dt(lstdel)}).\n"
    else:
        res += f"Never deleted.\n"

    res += "\n"

    res += "In Challenge Mode,\n"
    if appeared > 0:
        res += f"It has appeared for {appeared} times,\n"
        if mem > 0:
            if fgt == 0:
                res += f"You remembered it every time. Good job!\n"
            else:
                res += f"While recorded as memorized for {mem} times,\n"
                if fgt > 0:
                    res += f"And recorded as forgotten for {fgt} times.\n"
        else:
            res += f"You never memorized it.\n"
        
        res += "\n"

        # res += f"In the last 30 days,"
        # if lst30d > 0:
        #     res += f"it appeared {lst30d} times\nAnd you remembered it for {lst30dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        # if lst7d > 0:
        #     res += f"it appeared {lst7d} times\nAnd you remembered it for {lst7dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        # if lst1d > 0:
        #     res += f"it appeared {lst1d} times\nAnd you remembered it for {lst1dmem} times.\n"
        # else:
        #     res += f"it hasn't appeared."
        
        res += f"The last time it appeared is at\n{ts2dt(lst)},\n"
        if lstmem < lstfgt:
            res += "And you forgot it that time.\n"
        else:
            res += "And you remembered it that time.\n"

        res += "\n"

        res += f"Normally, it will appear again at around\n{ts2dt(nxt)},\n"
        res += f"If you do Challenge Mode at that time.\n"

        res += "\n"
        res += "[Time in UTC + 0]"

    else:
        res += f"It hasn't appeared yet."
    
    return json.dumps({"msg":res})

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
        cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE wordId{op}{current} AND {statusRequirement} ORDER BY wordId {order} LIMIT 1")
        d = cur.fetchall()
        if len(d) == 0: # no matching results, then find result from first / end
            cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE {statusRequirement} ORDER BY wordId {order} LIMIT 1")
            d = cur.fetchall()

    elif moveType == 0:
        cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE {statusRequirement} ORDER BY RANDOM() LIMIT 1")
        d = cur.fetchall()

    if len(d) == 0:
        abort(404)

    (wordId, word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    splitLine = int(request.args["splitLine"])
    translation = insert_newlines(translation, splitLine)

    return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

rnd=[1,1,1,1,1,1,1,2,2,2,2,2,2,3,3,3,3,3,3,4]
def getChallengeWordId(nofour = False):
    wordId = -1

    # just an interesting random function
    rnd.remove(4)
    random.shuffle(rnd)
    t = rnd[random.randint(0,len(rnd)-1)]
    rnd.append(4)
    
    if t == 1:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} ORDER BY wordId ASC")
        d1 = cur.fetchall()
        cur.execute(f"SELECT wordId FROM WordList WHERE status = 2 ORDER BY RANDOM()")
        d2 = cur.fetchall()
        for dd in d2:
            if (dd[0],) in d1:
                wordId = dd[0]
                break

        if wordId == -1:
            t = 2
    
    if t == 2:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE nextChallenge <= {int(time.time())} AND nextChallenge != 0 ORDER BY nextChallenge ASC")
        d1 = cur.fetchall()
        cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 ORDER BY wordId ASC")
        d2 = cur.fetchall()
        for dd in d1:
            if (dd[0],) in d2:
                wordId = dd[0]
                break
        
        if wordId == -1:
            t = 3
    
    if t == 3:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE nextChallenge = 0 ORDER BY RANDOM() ASC")
        d1 = cur.fetchall()
        cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 ORDER BY wordId ASC")
        d2 = cur.fetchall()
        for dd in d1:
            if (dd[0],) in d2:
                wordId = dd[0]
                break
        
        if wordId == -1:
            t = 5
    
    if t == 5:
        cur.execute(f"SELECT wordId FROM ChallengeData WHERE lastChallenge <= {int(time.time()) - 1200} AND nextChallenge != 0 ORDER BY nextChallenge ASC")
        d1 = cur.fetchall()
        cur.execute(f"SELECT wordId FROM WordList WHERE status = 1 ORDER BY wordId ASC")
        d2 = cur.fetchall()
        for dd in d1:
            if (dd[0],) in d2:
                wordId = dd[0]
                break
        
        if wordId == -1:
            t = 4
    
    if t == 4:
        cur.execute(f"SELECT wordId FROM WordList WHERE status = 3 ORDER BY RANDOM() LIMIT 1")
        d = cur.fetchall()

        if len(d) != 0:
            wordId = d[0][0]
        
        if wordId == -1:
            wordId = getChallengeWordId(nofour = True)
    
    return wordId

@app.route("/getNextChallenge")
def getNextChallenge():
    wordId = getChallengeWordId()

    splitLine = int(request.args["splitLine"])
    if wordId == -1:
        return json.dumps({"wordId": wordId, "word": "Out of challenge", "translation": insert_newlines("You are super!\nNo more challenge can be done!",splitLine), "status": 1})

    cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId}")
    d = cur.fetchall()
    (word, translation, status) = d[0]
    word = decode(word)
    translation = decode(translation)

    translation = insert_newlines(translation, splitLine)

    return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

# addtime = [20 minute, 1 hour, 3 hour, 8 hour, 1 day, 2 day, 5 day, 10 day]
addtime = [300, 1200, 3600, 10800, 28800, 86400, 172800, 432000, 864000]
@app.route("/updateChallengeRecord")
def updateChallengeRecord():
    wordId = int(request.args["wordId"])
    memorized = int(request.args["memorized"])
    getNext = int(request.args["getNext"])
    ts = int(time.time())

    cur.execute(f"SELECT memorized, timestamp FROM ChallengeRecord WHERE wordId = {wordId} ORDER BY timestamp DESC")
    d = cur.fetchall()

    cur.execute(f"INSERT INTO ChallengeRecord VALUES ({wordId},{memorized},{ts})")
    cur.execute(f"UPDATE ChallengeData SET lastChallenge = {ts} WHERE wordId = {wordId}")

    if memorized == 1:
        tot = 1
        for dd in d:
            if dd[0] == 1:
                tot += 1
        if tot > 8:
            tot = 8
        cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[tot]} WHERE wordId = {wordId}")

    elif memorized == 0:
        cur.execute(f"UPDATE ChallengeData SET nextChallenge = {ts + addtime[0]} WHERE wordId = {wordId}")
    
    conn.commit()

    if getNext == 1:
        wordId = getChallengeWordId()

        splitLine = int(request.args["splitLine"])
        if wordId == -1:
            return json.dumps({"wordId": wordId, "word": "Out of challenge", "translation": insert_newlines("You are super! No more challenge can be done!",splitLine), "status": 1})

        cur.execute(f"SELECT word, translation, status FROM WordList WHERE wordId = {wordId}")
        d = cur.fetchall()
        (word, translation, status) = d[0]
        word = decode(word)
        translation = decode(translation)

        translation = insert_newlines(translation, splitLine)

        return json.dumps({"wordId": wordId, "word": word, "translation": translation, "status": status})

    else:
        return json.dumps({"success": True})


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

@app.route("/addWord")
def addWord():
    word = encode(request.form["word"])
    translation = encode(request.form["translation"])

    cur.execute(f"SELECT wordId FROM WordList ORDER BY wordId DESC LIMIT 1")
    d = cur.fetchall()
    if len(d) != 0:
        wordId = d[0][0]

    cur.execute(f"INSERT INTO WordList VALUES ({wordId+1},'{word}','{translation}',1)")
    cur.execute(f"INSERT INTO ChallengeData VALUES ({wordId+1},0,-1)")
    updateWordStatus(wordId+1,-1)
    updateWordStatus(wordId+1,1)
    conn.commit()

    return json.dumps({"success":True})

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
            if list(uploaded.keys()).count("Word") != 1 or list(uploaded.keys()).count("Translation")!=1:
                os.system(f"rm -f /tmp/data{ts}.xlsx")
                return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Translation'!")
        except:
            os.system(f"rm -f /tmp/data{ts}.xlsx")
            return render_template("import.html", MESSAGE = "Invalid format! The columns must contain 'Word','Translation'!")
        
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
            if type(newlist['Translation'][i]) != str:
                newlist['Translation'][i] = "[Unknown translation]"

            cur.execute(f"INSERT INTO WordList VALUES ({wordId}, '{encode(newlist['Word'][i])}', '{encode(newlist['Translation'][i])}', {status})")
            cur.execute(f"INSERT INTO ChallengeData VALUES ({wordId}, 0, -1)")

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
            cur.execute(f"SELECT word, translation, status FROM WordList")
            d = cur.fetchall()
            if len(d) == 0:
                return render_template("export.html", MESSAGE = "Empty word list!")
            
            xlsx = pd.DataFrame()
            for dd in d:
                word = pd.DataFrame([[decode(dd[0]), decode(dd[1]), StatusToStatusText[dd[2]]]],columns=["Word","Translation","Status"],index=[len(d)])
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