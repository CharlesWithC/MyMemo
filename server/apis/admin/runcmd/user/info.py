# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from db import newconn
from functions import *

def get_user_info(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 2:
        return {"success": False, "msg": f"Usage: get_user_info [userId]\nGet detailed user info of [userId]"}
    
    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    cur.execute(f"SELECT username, email, inviteCode, inviter FROM UserInfo WHERE userId = {uid}")
    d = cur.fetchall()
    banned = False
    if len(d) == 0:
        cur.execute(f"SELECT username, email, inviteCode, inviter FROM UserInfo WHERE userId = {-uid}") # check banned
        d = cur.fetchall()

        if len(d) == 0:
            return {"success": False, "msg": f"User not found!"}
        
        banned = True
    
    d = d[0]
    d = list(d)
    d[0] = decode(d[0])

    inviter = "Unknown"
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {d[3]}")
    t = cur.fetchall()
    if len(t) > 0:
        inviter = decode(t[0][0])
    if inviter == "default":
        inviter = "/"

    cnt = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {abs(uid)}")
    t = cur.fetchall()
    if len(t) > 0:
        cnt = t[0][0]

    regts = 0
    cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {abs(uid)} AND event = 'register'")
    t = cur.fetchall()
    if len(t) > 0:
        regts = t[0][0]

    msg = ""
    if banned:
        msg += "Account has been banned\n"
    
    if sessions.CheckDeletionMark(uid):
        msg += "Account deactivated! and marked for deletion\n"

    return {"success": True, "msg": f"{d[0]} (UID: {uid})\nEmail: {decode(d[1])}\nInvitation Code: {d[2]}\nInviter: {inviter} (UID: {d[3]})\nQuestion Count: {cnt}\nAccount age: {CalculateAge(regts)} day(s)\n{msg}"}

def get_user_count(userId, command):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM UserInfo")
    tot = 0
    d = cur.fetchall()
    if len(d) != 0:
        tot = d[0][0]
        
    cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId > 0")
    cnt = 0
    d = cur.fetchall()
    if len(d) != 0:
        cnt = d[0][0]
    
    cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE username = '{encode('@deleted')}' AND userId > 0")
    deled = 0
    d = cur.fetchall()
    if len(d) != 0:
        deled = d[0][0]

    cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId < 0")
    banned = 0
    d = cur.fetchall()
    if len(d) != 0:
        banned = d[0][0]
    
    marked_deletion = sessions.CountDeletionMark()
    cnt -= marked_deletion
    
    return {"success": True, "msg": f"Total user: {tot}\nActive user: {cnt - deled}\nBanned / Banned & Deleted user: {banned}\nDisabled (Pending deletion) user: {marked_deletion}\nDeleted user: {deled}"}
