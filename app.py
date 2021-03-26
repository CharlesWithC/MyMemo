from flask import Flask,render_template,request,abort
import os,random,json,time,hashlib,threading

wordlist=[]
import pandas as pd
data=pd.read_excel("./data.xlsx")
for i in range(len(data["Word"])):
    word=""
    pronouncation=data['Pronounciation'][i]
    if str(pronouncation)=="nan":
        word=data['Word'][i]
    else:
        word=data['Word'][i]
    wordlist.append((word,data['Definition'][i]))

taglist=open("tagdata","r").read().replace("\n\n","\n").split("\n")

untaggedWordList=wordlist.copy()
for i in range(len(wordlist)):
    info=wordlist[i]
    if info[0] in taglist:
        untaggedWordList.remove(info)

def insert_newlines(string, every=16):
    return '\n'.join(string[i:i+every] for i in range(0, len(string), every))

app=Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getwordid")
def getwordid():
    word=request.args["word"].replace("%20"," ")
    showtagged=int(request.args["showtagged"])
    wl=[]
    if showtagged:
        wl=wordlist
    else:
        wl=untaggedWordList
    for i in range(len(wl)):
        if wl[i][0].startswith(word):
            return json.dumps({"wordid":i})
    return json.dumps({"wordid":-1})

@app.route("/getword")
def getword():
    wordid=int(request.args["wordid"])
    showtagged=int(request.args["showtagged"])
    splitline=int(request.args["splitline"])

    wl=[]
    if showtagged:
        wl=wordlist
    else:
        wl=untaggedWordList

    if wordid>=0 and len(wl)>wordid:
        word=wl[wordid][0]

        definition=wl[wordid][1]
        if definition.find("\n")!=-1:
            d=definition.split("\n")
            definition=d[0]+"\n"+insert_newlines('\n'.join(d[1:]),splitline)
        else:
            definition=insert_newlines(definition,splitline)
        
        tagged=False
        if word in taglist:
            tagged=True

        return json.dumps({"wordid":wordid,"word":word,"definition":definition,"tagged":tagged})
    else:
        abort(404)

@app.route("/tagword")
def tagword():
    wordid=int(request.args["wordid"])
    showtagged=int(request.args["showtagged"])
    wl=[]
    if showtagged:
        wl=wordlist
    else:
        wl=untaggedWordList
    word=wl[wordid][0]
    if not word in taglist:
        taglist.append(word)
        open("tagdata","a").write(word+"\n")
        untaggedWordList.remove(wl[wordid])
        return json.dumps({"tagged":True})
    else:
        taglist.remove(word)
        f=open("tagdata","w")
        for tag in taglist:
            f.write(tag+"\n")
        f.close()
        untaggedWordList.append(wl[wordid])
        return json.dumps({"tagged":False})

@app.route("/getwordcount")
def getwordcount():
    return json.dumps({"count":len(wordlist)})

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

def restart():
    time.sleep(1)
    os.system("python3 app.py &")
    os.system("./app &")
    os.system(f"kill -KILL {os.getpid()}")

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
            if len(uploaded.keys())!=3 or not (uploaded.keys()==['Word','Pronounciation','Definition']).all():
                os.system(f"rm -f /tmp/data{ts}.xlsx")
                return render_template("upload.html",MESSAGE="Invalid format! The headings must be 'Word','Pronounciation','Definition'!")
        except:
            os.system(f"rm -f /tmp/data{ts}.xlsx")
            return render_template("upload.html",MESSAGE="Invalid format! The headings must be 'Word','Pronounciation','Definition'!")
        
        os.system(f"mv /tmp/data{ts}.xlsx ./data.xlsx")

        threading.Thread(target=restart).start()

        return render_template("upload.html",MESSAGE="Data uploaded!")
    else:
        return render_template("upload.html",MESSAGE="")

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run("127.0.0.1",8888)