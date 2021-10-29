# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time, math
import json
import validators
import sqlite3

from app import app
from functions import *
import sessions


conn = sqlite3.connect("database.db", check_same_thread = False)


def validateToken(userId, token):
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0 or d[0][0] == "@deleted":
        return False
    
    return sessions.validateToken(userId, token)


##########
# Admin API

@app.route("/api/admin/restart", methods = ['POST'])
def apiAdminRestart():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        abort(401)
    
    if os.path.exists("/tmp/WordMemoLastManualRestart"):
        lst = int(open("/tmp/WordMemoLastManualRestart","r").read())
        if int(time.time()) - lst <= 1800:
            return json.dumps({"success": False, "msg": "Only one restart in each 30 minutes is allowed!"})
    
    open("/tmp/WordMemoLastManualRestart","w").write(str(int(time.time())))

    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
    sys.exit(0)


# Make sure this route is protected by reverse proxy (nginx / apache) authentication
# Otherwise remove the route to prevent your server from being attacked

@app.route("/admin/restart", methods = ['GET'])
def adminRestart():
    if os.path.exists("/tmp/WordMemoLastManualRestart"):
        lst = int(open("/tmp/WordMemoLastManualRestart","r").read())
        if int(time.time()) - lst <= 1800:
            return "Only one restart in each 30 minutes is allowed!"
    
    open("/tmp/WordMemoLastManualRestart","w").write(str(int(time.time())))

    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
    sys.exit(0)

@app.route("/api/admin/command", methods = ['POST'])
def apiAdminCommand():
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)
        
    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)

    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {userId}")
    if len(cur.fetchall()) == 0:
        abort(401)
    
    command = request.form["command"].split(" ")
    if command[0] == "get_user_info":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": f"Usage: get_user_info [userId]\nGet detailed user info of [userId]"})
        
        uid = abs(int(command[1]))
        
        cur.execute(f"SELECT username, email, inviteCode, inviter FROM UserInfo WHERE userId = {uid}")
        d = cur.fetchall()
        banned = False
        if len(d) == 0:
            cur.execute(f"SELECT username, email, inviteCode, inviter FROM UserInfo WHERE userId = {-uid}") # check banned
            d = cur.fetchall()

            if len(d) == 0:
                return json.dumps({"success": False, "msg": f"User not found!"})
            
            banned = True
        
        d = d[0]

        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {d[3]}")
        inviter = cur.fetchall()[0][0]

        cur.execute(f"SELECT COUNT(*) FROM WordList WHERE userId = {uid}")
        cnt = cur.fetchall()[0][0]

        cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {uid} AND event = 'register'")
        regts = cur.fetchall()[0][0]
        age = math.ceil((time.time() - regts) / 86400)

        msg = ""
        if banned:
            msg += "Account has been banned\n"

        return json.dumps({"success": True, "msg": f"{d[0]} (UID: {uid})\nEmail: {d[1]}\nInvitation Code: {d[2]}\nInviter: {inviter} (UID: {d[3]})\nWord Count: {cnt}\nAccount age: {age} day(s)\n{msg}"})
    
    elif command[0] == "create_user":
        if len(command) != 4:
            return json.dumps({"success": False, "msg": f"Usage: create_user [username] [email] [password]\nCreate a user by admin, user will be shown as invited by this admin"})
        
        username = command[1]
        email = command[2]
        password = command[3]
        inviter = userId # inviter is admin
        
        if not username.replace("_","").isalnum():
            return json.dumps({"success": False, "msg": "Username can only contain alphabets, digits and underscore!"})
        if validators.email(email) != True:
            return json.dumps({"success": False, "msg": "Invalid email!"})

        cur.execute(f"SELECT username FROM UserInfo WHERE username = '{username}'")
        if len(cur.fetchall()) != 0:
            return json.dumps({"success": False, "msg": "Username already registered!"})

        password = hashpwd(password)

        inviteCode = genCode()

        uid = 1
        try:
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 1")
            uid = cur.fetchall()[0][0]
            cur.execute(f"UPDATE IDInfo SET nextId = {uid + 1} WHERE type = 1")

            cur.execute(f"INSERT INTO UserInfo VALUES ({uid}, '{username}', '{email}', '{encode(password)}', {inviter}, '{inviteCode}')")
            conn.commit()
        except:
            sessions.errcnt += 1
            return json.dumps({"success": False, "msg": "Unknown error occured. Try again later..."})

        cur.execute(f"INSERT INTO UserEvent VALUES ({uid}, 'register', {int(time.time())})")
        conn.commit()

        return json.dumps({"success": True, "msg": f"User registered (UID: {uid})"})
    
    elif command[0] == "delete_user":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: delete_user [userId]\nThe account must be marked as deletion first, and admin will be able to bring the deletion schedule forward"})

        uid = int(command[1])
        ok = sessions.DeleteAccountNow(uid)

        if ok == -1:
            return json.dumps({"success": False, "msg": "Account not marked for deletion!"})
        
        elif ok == 0:
            cur.execute(f"UPDATE UserInfo SET username = '@deleted' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordList WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBook WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBookData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM WordBookShare WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeRecord WHERE userId = {uid}")
            cur.execute(f"DELETE FROM StatusUpdate WHERE userId = {uid}")
            return json.dumps({"success": False, "msg": "Account deleted"})
    
    elif command[0] == "set_previlege":
        if len(command) != 4:
            return json.dumps({"success": False, "msg": "Usage: set_previlege [userId] [item] [value]\nAdd [item] previlege for user [userId] ([item] can be word_limit)\nIf previlege exists, then update it"})

        uid = int(command[1])
        item = command[2]
        value = int(command[3])

        if not item in ['word_limit', 'word_book_limit', 'allow_group_creation', 'group_member_limit']:
            return json.dumps({"success": False, "msg": f"Unknown previlege item: {item}. Acceptable item list: word_limit"})

        cur.execute(f"SELECT * FROM Previlege WHERE userId = {uid} AND item = '{item}'")
        if len(cur.fetchall()) == 0:
            cur.execute(f"INSERT INTO Previlege VALUES ({uid}, '{item}', {value})")
        else:
            cur.execute(f"UPDATE Previlege SET value = {value} WHERE userId = {uid} AND item = '{item}'")
        conn.commit()

        return json.dumps({"success": True, "msg": "Previlege set"})
    
    elif command[0] == "remove_previlege":
        if len(command) != 3:
            return json.dumps({"success": False, "msg": "Usage: remove_previlege [userId] [item]\nDelete [item] previlege from user [userId]"})

        uid = int(command[1])
        item = command[2]

        if not item in ['word_limit', 'word_book_limit', 'allow_group_creation', 'group_member_limit']:
            return json.dumps({"success": False, "msg": f"Unknown previlege item: {item}. Acceptable item list: word_limit"})

        cur.execute(f"SELECT * FROM Previlege WHERE userId = {uid} AND item = '{item}'")
        if len(cur.fetchall()) != 0:
            cur.execute(f"DELETE FROM Previlege WHERE userId = {uid} AND item = '{item}'")
            conn.commit()
            return json.dumps({"success": True, "msg": "Previlege removed for this user"})
        else:
            return json.dumps({"success": False, "msg": "This user doesn't have this previlege!"})

    elif command[0] == "ban_account":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: ban_account [userId]\nBan account"})
        
        uid = int(command[1])

        if uid < 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if uid == userId:
            return json.dumps({"success": False, "msg": "You cannot ban yourself!"})

        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {uid}")
        if len(cur.fetchall()) == 0:
            cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
            if len(cur.fetchall()) == 0:
                return json.dumps({"success": False, "msg": "Account doesn't exist!"})
            else:
                return json.dumps({"success": False, "msg": "Account already banned!"})
        
        cur.execute(f"UPDATE UserInfo SET userId = {-uid} WHERE userId = {uid}")
        conn.commit()

        return json.dumps({"success": False, "msg": f"Banned user {uid}"})

    elif command[0] == "unban_account":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: unban_account [userId]\nUnban account"})
        
        uid = int(command[1])

        if uid <= 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})

        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"success": False, "msg": "Account isn't banned!"})
            
        else:
            cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-uid}")
            if len(cur.fetchall()) == 0:
                return json.dumps({"success": False, "msg": "Account doesn't exist!"})
            else:
                cur.execute(f"UPDATE UserInfo SET userId = {uid} WHERE userId = {-uid}")
                conn.commit()
                return json.dumps({"success": False, "msg": f"Unbanned user {uid}"})

    elif command[0] == "get_user_count":
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
        
        cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE username = '@deleted' AND userId > 0")
        deled = 0
        d = cur.fetchall()
        if len(d) != 0:
            deled = d[0][0]

        cur.execute(f"SELECT COUNT(*) FROM UserInfo WHERE userId < 0")
        banned = 0
        d = cur.fetchall()
        if len(d) != 0:
            banned = d[0][0]
        
        return json.dumps({"success": True, "msg": f"Total user: {tot}\nActive user: {cnt - deled}\nBanned / Banned & Deleted user: {banned}\nDeleted user: {deled}"})

    else:
        return json.dumps({"success": False, "msg": "Unknown command"})