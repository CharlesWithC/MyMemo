from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from subprocess import Popen, PIPE
from fastapi import FastAPI, Request
import uvicorn

import time
import os
import json
import bcrypt

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
    
def checkpwd(password, hsh):
    return bcrypt.checkpw(password.encode(),hsh.encode())

app = FastAPI()

@app.get("/ping")
async def ping():
    return {"time": time.time()}

@app.post("/send")
async def sm(request: Request):
    try:
        form = await request.form()
        if not checkpwd(config.key, form["key"]):
            return {"success": False}
        
        msg = MIMEMultipart("alternative")
        msg["From"] = form["from"]
        msg["To"] = form["to"]
        msg["Subject"] = form["subject"]
        plain = MIMEText(form["plain"], 'plain')
        msg.attach(plain)
        html = MIMEText(form["html"], 'html')
        msg.attach(html)

        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(msg.as_bytes())
        return {"success": True}

    except:
        import traceback
        traceback.print_exc()
        return {"success": False}

if __name__ == "__main__":
    uvicorn.run("main:app", host = config.server_ip, port = config.server_port)