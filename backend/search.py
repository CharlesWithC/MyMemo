# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
from fuzzywuzzy import process
from multiprocessing import Process

from db import newconn
import os, time, json
import base64

def decode(s):
    try:
        return base64.b64decode(s.encode()).decode()
    except:
        print(f"Unable to decode {s}")
        return ""

class Dict2Obj(object):
    def __init__(self, d):
        for key in d:
            if type(d[key]) is dict:
                data = Dict2Obj(d[key])
                setattr(self, key, data)
            else:
                setattr(self, key, d[key])

config = None
if os.path.exists("./config.json"):
    config_txt = open("./config.json","r").read()
    config = Dict2Obj(json.loads(config_txt))

app = FastAPI()

lst = {}
lstupd = 0
def UpdateData():
    conn = newconn()
    cur = conn.cursor()
    global lst, lstupd
    cur.execute(f"SELECT discoveryId, title, description, publisherId, type, bookId, pin, views, likes FROM Discovery ORDER BY pin DESC, likes DESC, views DESC")
    t = cur.fetchall()
    lst = {}
    for tt in t:
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {tt[3]}")
        p = cur.fetchall()
        username = ""
        if len(p) > 0 and not p[0][0] == "@deleted" and not decode(p[0][0]) == "@deleted":
            username = p[0][0]
        if decode(tt[1]) in lst.keys():
            lst[decode(tt[1]) + " " + username].append(tt)
        else:
            lst[decode(tt[1]) + " " + username] = [tt]
    lstupd = time.time()

top = []
toplst = 0

def GetTop():
    conn = newconn()
    cur = conn.cursor()
    global top, toplst
    cur.execute(f"SELECT discoveryId FROM Discovery ORDER BY likes DESC LIMIT 3")
    t = cur.fetchall()
    top = []
    for tt in t:
        top.append(tt[0])
    toplst = int(time.time())

@app.post("/search/discovery")
async def apiSearchDiscovery(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    ret = []

    global lst, lstupd
    if time.time() - lstupd > 30:
        if lstupd == 0:
            UpdateData()
        else:
            background_tasks.add_task(UpdateData)
        
    limit = form["search"][:32]
    limit = ''.join(e for e in limit if e.isalnum())
    limit = limit.replace(" ","")

    if limit == "":
        for d in lst.keys():
            for dd in lst[d]:
                ret.append(dd)
        return {"result": ret}

    res = process.extract(limit, lst.keys(), limit = None)
    for d in res:
        if d[1] >= 10 and d[0] in lst.keys():
            for dd in lst[d[0]]:
                ret.append(dd)
    
    return {"result": ret}

@app.post("/search/discoveryTop")
async def apiGetDiscoveryTop(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()

    global top, toplst
    if time.time() - toplst > 30:
        if toplst == 0:
            GetTop()
        else:
            background_tasks.add_task(GetTop)
    
    return {"top": top}

if __name__ == "__main__":
    uvicorn.run("search:app", host = config.search_server_ip, port = config.search_server_port)