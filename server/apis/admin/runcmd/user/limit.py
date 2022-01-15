# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

# Admin commands: User Limit

from fastapi import Request, HTTPException, BackgroundTasks
import time

from app import app, config
from db import newconn
from functions import *
import sessions

def mute(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 3:
        return {"success": False, "msg": "Usage: mute [userId] [duration]\nMute [userId] for [duration] days\nTo mute forever, set [duration] to -1"}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}

    value = int(command[2])

    if uid == userId:
        return {"success": False, "msg": "You cannot mute yourself!"}

    if value != -1:
        value = int(time.time()) + 86400 * value

    cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = 'mute'")
    if len(cur.fetchall()) == 0:
        cur.execute(f"INSERT INTO Privilege VALUES ({uid}, 'mute', '{value}')")
    else:
        cur.execute(f"UPDATE Privilege SET value = '{value}' WHERE userId = {uid} AND item = 'mute'")
    conn.commit()

    return {"success": True, "msg": "User muted"}
    
def unmute(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 2:
        return {"success": False, "msg": "Usage: unmute [userId]\nUnmute [userId]"}
    
    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}

    cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = 'mute'")
    if len(cur.fetchall()) != 0:
        cur.execute(f"DELETE FROM Privilege WHERE userId = {uid} AND item = 'mute'")
        conn.commit()
        return {"success": True, "msg": "User unmuted!"}
    else:
        return {"success": False, "msg": "User not muted!"}
        
def ban(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) < 3:
        return {"success": False, "msg": "Usage: ban [userId] [reason]\nBan account"}
    
    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid <= 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if uid == userId:
        return {"success": False, "msg": "You cannot ban yourself!"}

    cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {uid}")
    if len(cur.fetchall()) == 0:
        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
        if len(cur.fetchall()) == 0:
            return {"success": False, "msg": "Account doesn't exist!"}
        else:
            return {"success": False, "msg": "Account already banned!"}

    reason = encode(" ".join(command[2:]))
    cur.execute(f"UPDATE UserInfo SET userId = {-uid} WHERE userId = {uid}")
    cur.execute(f"INSERT INTO BanReason VALUES ({uid}, '{reason}')")
    conn.commit()

    return {"success": True, "msg": f"Banned user {uid}"}

def unban(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 2:
        return {"success": False, "msg": "Usage: unban [userId]\nUnban account"}
    
    uid = 0
    if not command[1].isdigit():
        uid = abs(usernameToUid(encode(command[1])))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}

    cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
    if len(cur.fetchall()) == 0:
        return {"success": False, "msg": "Account isn't banned!"}
        
    else:
        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
        if len(cur.fetchall()) == 0:
            return {"success": False, "msg": "Account doesn't exist!"}
        else:
            cur.execute(f"UPDATE UserInfo SET userId = {uid} WHERE userId = {-uid}")
            cur.execute(f"DELETE FROM BanReason WHERE userId = {uid}")
            conn.commit()
            return {"success": True, "msg": f"Unbanned user {uid}"}
