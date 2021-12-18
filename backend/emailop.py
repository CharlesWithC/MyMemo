# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os
import json
import telnetlib
import datetime
import time
from email import utils
import dkim

config = None
if os.path.exists("./config.json"):
    config_txt = open("./config.json","r").read()
    config = json.loads(config_txt)
    
postfix = config["postfix_host"]
helo = config["helo"]
icon_url = config["icon_url"]
host = postfix[:postfix.find(":")]
port = postfix[postfix.find(":")+1:]
mail_domain = config["mail_domain"]
mail_from = config["mail_from"]
mail_contact = config["mail_contact"]
dkim_key_path = config["dkim_key_path"]
dkim_selector = config["dkim_selector"]

import random
st="abcdefghjkmnpqrstuvwxy3456789ABCDEFGHJKMNPQRSTUVWXY"
def genCode(length = 8):
    ret = ""
    for _ in range(length):
        ret += st[random.randint(0,len(st)-1)]
    return ret 

def telnetMail(mail_from, mail_to, mail_from_name, mail_to_name, subject, plain, html):
    tn = telnetlib.Telnet(host, port)
    tn.read_until(b"220")
    tn.write(f"HELO {helo}\n".encode())
    tn.read_until(b"250")
    boundary = genCode()
    nowdt = datetime.datetime.now()
    nowtuple = nowdt.timetuple()
    nowtimestamp = time.mktime(nowtuple)
    ts = utils.formatdate(nowtimestamp)

    msgdata = f"""MIME-Version: 1.0
From: {mail_from_name} <{mail_from}>
To: {mail_to_name} <{mail_to}>
Date: {str(ts)}
Message-ID: {utils.make_msgid()}
Subject: {subject}

Content-type: text/html;boundary="{boundary}";charset=utf-8

{html}

--{boundary}

Content-Type: text/plain;charset=utf-8

{plain}

"""

    if not dkim_key_path == "" and os.path.exists(dkim_key_path):
        dkim_pvtkey = open(dkim_key_path).read()
        headers = [b"Message_ID",b"Date",b"Subject",b"To", b"From"]
        sig = dkim.sign(
            message=msgdata.encode(),
            selector=dkim_selector.encode(),
            domain=mail_domain.encode(),
            privkey=dkim_pvtkey.encode(),
            include_headers=headers,
        )
        msgdata = f"""MIME-Version: 1.0
From: {mail_from_name} <{mail_from}>
To: {mail_to_name} <{mail_to}>
Date: {str(ts)}
Message-ID: {utils.make_msgid()}
Subject: {subject}
Content-type: text/html;charset=utf-8
DKIM-Signature: {sig[len("DKIM-Signature: ") :].decode()}

{html}

"""

    s=f"""MAIL FROM: <{mail_from}>
RCPT TO: <{mail_to}>
DATA
{msgdata}

.

"""

    nowait = False
    for ss in s.split("\n"):
        if ss == "DATA":
            nowait = True
        if ss == ".":
            nowait = False
        tn.write((ss+"\n").encode())
        t = tn.read_very_eager().decode()
        if str(t).find("queued") != -1:
            return
        if not nowait:
            tn.read_until(b"250")

def sendVerification(mail_to, username, vtype, note, expire, link):
    data = "<!DOCTYPE html><html>\n"
    data += "<head><style>h2{font-size:1.6em}</style></head>\n"
    data += "<body>\n"

    data += f"<img src='{icon_url}' style='width:2em;height:2em;float:right' alt='My Memo'>\n"

    data += f"<h2>{vtype}</h2>\n"
    data += f"<p>{note}</p>\n"
    if expire != -1:
        data += f"<p>The link will expire in {expire}.</p>\n"
    data += f"<p>Verification link: <a href='{link}'>{link}</a></p>\n"

    data += f"<br><br><hr>\n"
    data += f"<p style='font-size:0.6em;color:gray'>This is an automated email. Please do not reply to it. To contact, use <a href='mailto:{mail_contact}'>{mail_contact}</a>.</p>\n"
    data += f"<p style='font-size:0.6em;color:gray'>Copyright &copy; 2021 My Memo | Developed by Charles</a></p>\n"

    data += "</body>\n</html>\n"

    plain = "My Memo\n"
    plain += vtype.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += "Verification link: " + link + "\n"
    plain += "The link will expire in " + expire + "\n"
    plain += "\n"
    plain += f"This is an automated email. Please do not reply to it. To contact, use {mail_contact} .\n"
    plain += "Copyright &copy; 2021 My Memo | Developed by Charles."

    telnetMail(mail_from, mail_to, "My Memo", username, vtype, plain, data)

def sendNormal(mail_to, username, subject, content):
    data = "<!DOCTYPE html><html>\n"
    data += "<head><style>h2{font-size:1.6em}</style></head>\n"
    data += "<body>\n"

    data += f"<img src='{icon_url}' style='width:2em;height:2em;float:right' alt='My Memo'>\n"

    data += f"<h2>{subject}</h2>\n"
    data += f"<p>{content}</p>\n"

    data += f"<br><br><hr>\n"
    data += f"<p style='font-size:0.6em;color:gray'>This is an automated email. Please do not reply to it. To contact, use <a href='mailto:{mail_contact}'>{mail_contact}</a>.</p>\n"
    data += f"<p style='font-size:0.6em;color:gray'>Copyright &copy; 2021 My Memo | Developed by Charles</a></p>\n"
    
    data += "</body>\n</html>\n"

    plain = "My Memo\n"
    plain += subject.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += content.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += "\n"
    plain += f"This is an automated email. Please do not reply to it. To contact, use {mail_contact} .\n"
    plain += "Copyright &copy; 2021 My Memo | Developed by Charles."
    
    telnetMail(mail_from, mail_to, "My Memo", username, subject, plain, data)    