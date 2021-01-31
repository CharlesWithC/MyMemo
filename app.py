from flask import Flask,render_template,request
import random

wordlist=[]
import pandas as pd
data=pd.read_excel("data.xlsx")
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
            return str(i)
    return str(-1)

@app.route("/getword")
def getword():
    wordid=int(request.args["wordid"])
    showtagged=int(request.args["showtagged"])
    wl=[]
    if showtagged:
        wl=wordlist
    else:
        wl=untaggedWordList
    if wordid>=0 and len(wl)>wordid:
        return wl[wordid][0]
    else:
        return ""

@app.route("/getdefinition")
def getdefinition():
    wordid=int(request.args["wordid"])
    showtagged=int(request.args["showtagged"])
    wl=[]
    if showtagged:
        wl=wordlist
    else:
        wl=untaggedWordList
    if wordid>=0 and len(wl)>wordid:
        definition=wl[wordid][1]
        if definition.find("\n")!=-1:
            d=definition.split("\n")
            definition=d[0]+"\n"+insert_newlines('\n'.join(d[1:]))
        else:
            definition=insert_newlines(definition)
        return definition
    else:
        return ""

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
        return "Tagged"
    else:
        taglist.remove(word)
        f=open("tagdata","w")
        for tag in taglist:
            f.write(tag+"\n")
        f.close()
        untaggedWordList.append(wl[wordid])
        return "Untagged"

@app.route("/getwordcount")
def getwordcount():
    return str(len(wordlist))

app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.run("0.0.0.0")