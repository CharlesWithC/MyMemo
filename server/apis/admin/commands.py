# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request, HTTPException, BackgroundTasks
import os, sys, time
import uuid
import validators

from app import app, config
from db import newconn
from functions import *
from emailop import sendVerification
import main

import apis.admin.runcmd.user.info as info
import apis.admin.runcmd.user.manage as manage
import apis.admin.runcmd.user.limit as limit
import apis.admin.runcmd.user.privilege as privilege

##########
# Admin API

def restart():
    print("Requested to restart program! Restarting in 5 seconds...")
    time.sleep(5)
    os.execl(sys.executable, os.path.abspath(main.__file__), *sys.argv) 
    sys.exit(0)

def checkAdmin(userId):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        return False
    return True

@app.post("/api/admin/command")
async def apiAdminCommand(request: Request, background_tasks: BackgroundTasks):
    ip = request.client.host
    form = await request.form()
    conn = newconn()
    cur = conn.cursor()
    if not "userId" in form.keys() or not "token" in form.keys() or "userId" in form.keys() and (not form["userId"].isdigit() or int(form["userId"]) < 0):
        raise HTTPException(status_code=401)
        
    userId = int(form["userId"])
    token = form["token"]
    if not validateToken(userId, token):
        raise HTTPException(status_code=401)

    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        raise HTTPException(status_code=401)

    command = form["command"]
    command = decode(encode(command)) # remove html element
    if command == "check_admin":
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'execute_admin_command', {int(time.time())}, '{encode(f'Opened Admin Panel')}')")
        conn.commit()
        return {"success": True}
    else:
        cur.execute(f"INSERT INTO UserEvent VALUES ({userId}, 'execute_admin_command', {int(time.time())}, '{encode(f'Executed admin command: {command}')}')")
        conn.commit()

    command = command.split()

    if userId != 1 and not command[0] in ["get_user_info", "get_user_count", "create_user", "restart"]:
        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
            
        if checkAdmin(uid):
            return {"success": False, "msg": "Only site owner (UID: 1) can modify administrators."}

    if command[0] == "get_user_info":
        return info.get_user_info(userId, command)

    elif command[0] == 'get_user_count':
        return info.get_user_count(userId, command)

    elif command[0] == 'create_user':
        return manage.create_user(userId, command)

    elif command[0] == 'delete_pending':
        return manage.delete_pending(userId, command)

    elif command[0] == 'delete_user':
        return manage.delete_user(userId, command)
        
    elif command[0] == 'wipe_user':
        return manage.wipe_user(userId, command)
    
    elif command[0] == 'mute':
        return limit.mute(userId, command)
    
    elif command[0] == 'unmute':
        return limit.unmute(userId, command)

    elif command[0] == 'ban':
        return limit.ban(userId, command)
    
    elif command[0] == 'unban':
        return limit.unban(userId, command)
    
    elif command[0] == 'set_privilege':
        return privilege.set_privilege(userId, command)
    
    elif command[0] == 'remove_privilege':
        return privilege.remove_privilege(userId, command)
    
    elif command[0] == 'set_name_tag':
        return privilege.set_name_tag(userId, command)
    
    elif command[0] == 'reomve_name_tag':
        return privilege.reomve_name_tag(userId, command)
    
    elif command[0] == 'add_admin':
        if userId == 1:
            return privilege.add_admin(userId, command)
        else:
            return {"success": False, "msg": "Only site owner can add admins!"}
        
    elif command[0] == 'remove_admin':
        if userId == 1:
            return privilege.remove_admin(userId, command)
        else:
            return {"success": False, "msg": "Only site owner can remove admins!"}
            
    elif command[0] == "restart":
        if userId != 1:
            return {"success": False, "msg": "Only site owner can restart program!"}

        if os.path.exists("/tmp/MyMemoLastManualRestart"):
            lst = int(open("/tmp/MyMemoLastManualRestart","r").read())
            if int(time.time()) - lst <= 60:
                return {"success": False, "msg": "Only one restart is allowed within one minute!"}
        
        open("/tmp/MyMemoLastManualRestart","w").write(str(int(time.time())))

        background_tasks.add_task(restart)
        return {"success": True, "msg": "Server restarting..."}

    else:
        return {"success": False, "msg": "Unknown command"}