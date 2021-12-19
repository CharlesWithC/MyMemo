# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import os
import json
import requests
import bcrypt

config = None
if os.path.exists("./config.json"):
    config_txt = open("./config.json","r").read()
    config = json.loads(config_txt)
    
host = config["mail_remote"]
if host.endswith("/"):
    host = host[:-1]
icon_url = config["icon_url"]
mail_domain = config["mail_domain"]
mail_from = config["mail_from"]
mail_contact = config["mail_contact"]

import random
st="abcdefghjkmnpqrstuvwxy3456789ABCDEFGHJKMNPQRSTUVWXY"
def genCode(length = 8):
    ret = ""
    for _ in range(length):
        ret += st[random.randint(0,len(st)-1)]
    return ret 

def hashpwd(password):
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt(12)).decode()

def sendMail(mail_from, mail_to, mail_from_name, mail_to_name, subject, plain, html):
    key = hashpwd(config["mail_remote_key"])
    r = requests.post(host + "/send", data = {"key": key, "plain": plain, "html": html, "from": f"{mail_from_name} <{mail_from}>", "to": f"{mail_to_name} <{mail_to}>", "subject": subject})

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
    data += f"<p style='font-size:0.8em;color:gray'>This is an automated email. Please do not reply to it. To contact, use <a href='mailto:{mail_contact}'>{mail_contact}</a>.</p>\n"
    data += f"<p style='font-size:0.8em;color:gray'>Copyright &copy; 2021 My Memo | Developed by Charles</a></p>\n"

    data += "</body>\n</html>\n"

    plain = "My Memo\n"
    plain += vtype.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += "Verification link: " + link + "\n"
    plain += "The link will expire in " + expire + "\n"
    plain += "\n"
    plain += f"This is an automated email. Please do not reply to it. To contact, use {mail_contact} .\n"
    plain += "Copyright &copy; 2021 My Memo | Developed by Charles."

    sendMail(mail_from, mail_to, "My Memo", username, vtype, plain, data)

def sendNormal(mail_to, username, subject, content):
    data = "<!DOCTYPE html><html>\n"
    data += "<head><style>h2{font-size:1.6em}</style></head>\n"
    data += "<body>\n"

    data += f"<img src='{icon_url}' style='width:2em;height:2em;float:right' alt='My Memo'>\n"

    data += f"<h2>{subject}</h2>\n"
    data += f"<p>{content}</p>\n"

    data += f"<br><br><hr>\n"
    data += f"<p style='font-size:0.8em;color:gray'>This is an automated email. Please do not reply to it. To contact, use <a href='mailto:{mail_contact}'>{mail_contact}</a>.</p>\n"
    data += f"<p style='font-size:0.8em;color:gray'>Copyright &copy; 2021 My Memo | Developed by Charles</a></p>\n"
    
    data += "</body>\n</html>\n"
    
    plain = "My Memo\n"
    plain += subject.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += content.replace("<br>","\n").replace("\n\n","\n") + "\n"
    plain += "\n"
    plain += f"This is an automated email. Please do not reply to it. To contact, use {mail_contact} .\n"
    plain += "Copyright &copy; 2021 My Memo | Developed by Charles."
    
    sendMail(mail_from, mail_to, "My Memo", username, subject, plain, data)    