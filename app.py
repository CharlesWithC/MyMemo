from flask import Flask,render_template,request,abort
import os,random,json,time,hashlib,threading

import pandas as pd

wordlist=pd.DataFrame()
if os.path.exists("./data.xlsx"):
    wordlist=pd.read_excel("./data.xlsx")

def insert_newlines(string, every=16):
    return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

app=Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getWordID")
def getWordID():
    word=request.args["word"].replace("%20"," ")
    for i in range(len(wordlist)):
        if wordlist["Word"][i].startswith(word):
            return json.dumps({"wordid":i})
    return json.dumps({"wordid":-1})

@app.route("/getWord")
def getWord():
    wordid=int(request.args["wordid"])
    splitline=int(request.args["splitline"])

    if wordid>=0 and len(wordlist)>wordid:
        word=wordlist["Word"][wordid]

        definition=wordlist["Definition"][wordid]
        if definition.find("\n")!=-1:
            d=definition.split("\n")
            definition=d[0]+"\n"+insert_newlines('\n'.join(d[1:]),splitline)
        else:
            definition=insert_newlines(definition,splitline)

        status=wordlist["Status"][wordid]

        l={"Default":0,"Tagged":1,"Removed":2}
        return json.dumps({"wordid":wordid,"word":word,"definition":definition,"status":l[status]})
    else:
        abort(404)

@app.route("/getNext")
def getNext():
    wordid=-1
    current=int(request.args["wordid"])
    status=int(request.args["status"])
    movetype=request.args["movetype"]

    l=["Default","Tagged","Removed"]
    status=l[status]

    st=-1
    ed=-1
    stp=0
    if movetype=="previous":
        (st,ed,stp)=(current-1,-1,-1)
    elif movetype=="next":
        (st,ed,stp)=(current+1,len(wordlist),1)

    for i in range(st,ed,stp):
        if status=="Default" and wordlist["Status"][i] in ["Default","Tagged"] or \
            status=="Tagged" and wordlist["Status"][i] in ["Tagged"] or \
            status=="Removed" and wordlist["Status"][i] in ["Removed"]:
            wordid=i
            break

    if wordid==-1:
        abort(404)

    splitline=int(request.args["splitline"])

    word=wordlist["Word"][wordid]

    definition=wordlist["Definition"][wordid]
    if definition.find("\n")!=-1:
        d=definition.split("\n")
        definition=d[0]+"\n"+insert_newlines('\n'.join(d[1:]),splitline)
    else:
        definition=insert_newlines(definition,splitline)

    status=wordlist["Status"][wordid]

    l={"Default":0,"Tagged":1,"Removed":2}
    return json.dumps({"wordid":wordid,"word":word,"definition":definition,"status":l[status]})

@app.route("/getWordCount")
def getWordCount():
    return json.dumps({"count":len(wordlist)})

@app.route("/updateWordStatus")
def updateWordStatus():
    wordid=int(request.args["wordid"])
    status=int(request.args["status"])
    l=["Default","Tagged","Removed"]
    wordlist["Status"][wordid]=l[status]
    wordlist.to_excel('./data.xlsx',sheet_name='Data',index=False)
    return json.dumps({"succeed":True})

@app.route("/changepwd",methods=['GET','POST'])
def changepwd():
    if request.method=='POST':
        oldpwd=request.form["oldpwd"]
        newpwd=request.form["newpwd"]
        cfmpwd=request.form["cfmpwd"]

        oldhashed=hashlib.sha256(hashlib.sha256(oldpwd.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
        if oldhashed != open("./password","r").read().replace("\n",""):
            return render_template("changepwd.html",MESSAGE="Incorrect old password!")
        
        if newpwd!=cfmpwd:
            return render_template("changepwd.html",MESSAGE="New password and confirm password mismatch!")

        newhashed=hashlib.sha256(hashlib.sha256(newpwd.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
        open("./password","w").write(newhashed)

        return render_template("changepwd.html",MESSAGE="Password updated!")
    else:
        return render_template("changepwd.html",MESSAGE="")

@app.route("/upload",methods=['GET','POST'])
def upload():
    if request.method=='POST':
        password=request.form["password"]
        hashed=hashlib.sha256(hashlib.sha256(password.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
        if hashed != open("./password","r").read().replace("\n",""):
            return render_template("upload.html",MESSAGE="Invalid upload password!")

        if 'file' not in request.files:
            return render_template("upload.html",MESSAGE="Invalid upload! E1 No file found")
        file = request.files['file']
        if file.filename == '':
            return render_template("upload.html",MESSAGE="Invalid upload! E2 Empty file name")
        if not file.filename.endswith(".xlsx"):
            return render_template("upload.html",MESSAGE="Only .xlsx files are supported!")
        ts=int(time.time())
        file.save(f"/tmp/data{ts}.xlsx")

        try:
            uploaded=pd.read_excel(f"/tmp/data{ts}.xlsx")
            if len(uploaded.keys())!=2 or not (uploaded.keys()==['Word','Definition']).all():
                os.system(f"rm -f /tmp/data{ts}.xlsx")
                return render_template("upload.html",MESSAGE="Invalid format! The headings must be 'Word','Definition'!")
        except:
            os.system(f"rm -f /tmp/data{ts}.xlsx")
            return render_template("upload.html",MESSAGE="Invalid format! The headings must be 'Word','Definition'!")
        
        global wordlist
        uptype=request.form["uptype"]
        if uptype=="append":
            newlist=pd.read_excel(f"/tmp/data{ts}.xlsx")
            for i in range(0,len(newlist)):
                word=pd.DataFrame([[newlist["Word"][i],newlist["Definition"][i],"Default"]],columns=["Word","Definition","Status"],index=[len(wordlist)])
                wordlist=wordlist.append(word)
            wordlist.to_excel('./data.xlsx',sheet_name='Data',index=False)
        elif uptype=="overwrite":
            newlist=pd.read_excel(f"/tmp/data{ts}.xlsx")
            wordlist=pd.DataFrame() # clear old data
            for i in range(0,len(newlist)):
                word=pd.DataFrame([[newlist["Word"][i],newlist["Definition"][i],"Default"]],columns=["Word","Definition","Status"],index=[len(wordlist)])
                wordlist=wordlist.append(word)
            wordlist.to_excel('./data.xlsx',sheet_name='Data',index=False)

        os.system(f"rm -f /tmp/data{ts}.xlsx")

        return render_template("upload.html",MESSAGE="Data uploaded!")
    else:
        return render_template("upload.html",MESSAGE="")

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run("127.0.0.1",8888)