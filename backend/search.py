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
    while 1:
        conn = newconn()
        cur = conn.cursor()
        global lst, lstupd
        cur.execute(f"SELECT discoveryId, title, description, publisherId, type, bookId, pin FROM Discovery ORDER BY pin DESC, click DESC")
        t = cur.fetchall()
        lst = {}
        for tt in t:
            if decode(tt[1]) in lst.keys():
                lst[decode(tt[1]) + " " + decode(tt[2])].append(tt)
            else:
                lst[decode(tt[1]) + " " + decode(tt[2])] = [tt]
        lstupd = time.time()
        
        time.sleep(30)

top = []
toplst = 0

def GetTop():
    while 1:
        conn = newconn()
        cur = conn.cursor()
        global top, toplst
        cur.execute(f"SELECT discoveryId FROM DiscoveryLike GROUP BY discoveryId ORDER BY COUNT(likes) DESC LIMIT 3")
        t = cur.fetchall()
        top = []
        for tt in t:
            top.append(tt[0])
        toplst = int(time.time())

        time.sleep(30)

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
        
    limit = form["limit"][:32]
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
    updateDataProc = Process(target = UpdateData, daemon=True)
    updateDataProc.start()
    updateTopProc = Process(target = GetTop, daemon=True)
    updateTopProc.start()

    uvicorn.run("search:app", host = config.search_server_ip, port = config.search_server_port)