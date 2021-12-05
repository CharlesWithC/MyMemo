# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time, datetime, math
import json
import validators
import threading

from app import app, config
from db import newconn
from functions import *
import sessions

##########
# Admin API

@app.route("/api/admin/userList", methods = ['POST'])
def apiAdminUserList():
    conn = newconn()
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

    cur.execute(f"SELECT userId FROM AdminList")
    admins = cur.fetchall()
        
    cur.execute(f"SELECT userId, value FROM Privilege WHERE item = 'mute'")
    muted = cur.fetchall()
    
    cur.execute(f"SELECT userId, username, email, inviter, inviteCode FROM UserInfo")
    d = cur.fetchall()
    users = []
    for dd in d:
        dd = list(dd)
        dd[1] = decode(dd[1])

        status = "Active"
        if dd[0] < 0:
            status = "Banned"
        if dd[1] == "@deleted":
            status = "Deleted"
        if sessions.checkDeletionMark(dd[0]):
            status = "Deactivated"

        for mm in muted:
            if mm[0] == dd[0]:
                if int(mm[1]) == -1:
                    status += " , Muted forever"
                else:
                    status += " , Muted until " + str(datetime.datetime.fromtimestamp(int(mm[1])))

        if (dd[0],) in admins:
            status += " , Admin"
        
        inviterUsername = "Unknown"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) != 0:
            inviterUsername = decode(t[0][0])

        regts = 0
        cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {dd[0]} AND event = 'register'")
        t = cur.fetchall()
        if len(t) > 0:
            regts = t[0][0]
        age = math.ceil((time.time() - regts) / 86400)

        prv = ""
        cur.execute(f"SELECT item, value FROM Privilege WHERE userId = {dd[0]}")
        t = cur.fetchall()
        if len(t) == 0:
            prv = "/"
        else:
            for tt in t:
                prv += str(tt[0]) + ": " + str(tt[1])
                prv += ", "
            prv = prv[:-2]

        username = dd[1]
        cur.execute(f"SELECT tag, tagtype FROM UserNameTag WHERE userId = {dd[3]}")
        t = cur.fetchall()
        if len(t) > 0:
            username = f"<a href='/user?userId={dd[0]}'><span style='color:{t[0][1]}'>{username}</span></a> <span class='nametag' style='background-color:{t[0][1]}'>{decode(t[0][0])}</span>"
        else:
            username = f"<a href='/user?userId={dd[0]}'><span>{username}</span></a>"
        
        users.append({"userId": dd[0], "username": dd[1], "email": dd[2], "inviter": f"{inviterUsername} (UID: {dd[3]})", "inviteCode": dd[4], "age": age, "status": status, "privilege": prv})

    
    return json.dumps(users)

def restart():
    time.sleep(5)
    os.execl(sys.executable, os.path.abspath(__file__), *sys.argv) 
    sys.exit(0)

@app.route("/api/admin/command", methods = ['POST'])
def apiAdminCommand():
    conn = newconn()
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
    
    command = request.form["command"].split()
    if command[0] == "get_user_info":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": f"Usage: get_user_info [userId]\nGet detailed user info of [userId]"})
        
        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
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
        d = list(d)
        d[0] = decode(d[0])

        inviter = "Unknown"
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {d[3]}")
        t = cur.fetchall()
        if len(t) > 0:
            inviter = decode(t[0][0])

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
        age = math.ceil((time.time() - regts) / 86400)

        msg = ""
        if banned:
            msg += "Account has been banned\n"
        
        if sessions.CheckDeletionMark(uid):
            msg += "Account deactivated! and marked for deletion\n"

        return json.dumps({"success": True, "msg": f"{d[0]} (UID: {uid})\nEmail: {d[1]}\nInvitation Code: {d[2]}\nInviter: {inviter} (UID: {d[3]})\nQuestion Count: {cnt}\nAccount age: {age} day(s)\n{msg}"})
    
    elif command[0] == "create_user":
        if len(command) != 4:
            return json.dumps({"success": False, "msg": f"Usage: create_user [username] [email] [password]\nCreate a user by admin, user will be shown as invited by this admin"})
        
        username = command[1]
        email = command[2]
        password = command[3]
        inviter = userId # inviter is admin

        if " " in username or "(" in username or ")" in username or "[" in username or "]" in username or "{" in username or "}" in username \
            or "<" in username or ">" in username \
                or "!" in username or "@" in username or "'" in username or '"' in username or "/" in username or "\\" in username :
            return json.dumps({"success": False, "msg": "Username must not contain: spaces, ( ) [ ] { } < > ! @ ' \" / \\"})
    
        username = encode(username)
        if validators.email(email) != True:
            return json.dumps({"success": False, "msg": "Invalid email!"})

        cur.execute(f"SELECT username, email FROM UserInfo")
        t = cur.fetchall()
        for tt in t:
            if decode(tt[0]).lower() == decode(username).lower():
                return json.dumps({"success": False, "msg": "Username has been occupied!"})
            if tt[1].lower() == email.lower():
                return json.dumps({"success": False, "msg": "Email has already been registered!"})

        password = hashpwd(password)

        inviteCode = genCode()

        uid = 1
        try:
            cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 1")
            t = cur.fetchall()
            if len(t) > 0:
                uid = t[0][0]
            cur.execute(f"UPDATE IDInfo SET nextId = {uid + 1} WHERE type = 1")

            if len(username) >= 256:
                return json.dumps({"success": False, "msg": "Username too long!"})

            cur.execute(f"INSERT INTO UserInfo VALUES ({uid}, '{username}', '', '{email}', '{encode(password)}', {inviter}, '{inviteCode}', 99999)")
            conn.commit()
        except:
            sessions.errcnt += 1
            return json.dumps({"success": False, "msg": "Unknown error occured. Try again later..."})

        cur.execute(f"INSERT INTO UserEvent VALUES ({uid}, 'register', {int(time.time())}, '{encode('Birth of account')}')")
        conn.commit()

        return json.dumps({"success": True, "msg": f"User registered (UID: {uid})"})
    
    elif command[0] == "delete_user":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: delete_user [userId]\nThe account must be marked as deletion first, and admin will be able to bring the deletion schedule forward"})

        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if checkBanned(uid):
            uid = -uid
        
        ok = sessions.DeleteAccountNow(abs(uid))

        if ok == -1:
            cur.execute(f"SELECT inviter FROM UserInfo WHERE userId = {uid}")
            t = cur.fetchall()
            if len(t) != 0 and t[0][0] == userId: # created by this admin
                cur.execute(f"SELECT timestamp FROM UserEvent WHERE userId = {abs(uid)} AND event = 'register'")
                t = cur.fetchall()
                if len(t) != 0 and int(time.time()) - t[0][0] <= 7200:
                    cur.execute(f"UPDATE UserInfo SET username = '{encode('@deleted')}' WHERE userId = {uid}")
                    cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {uid}")
                    cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {uid}")
                    cur.execute(f"UPDATE UserInfo SET userId = {abs(uid)} WHERE userId = {uid}")
                    conn.commit()
                    return json.dumps({"success": False, "msg": "Revoked account creation!"})

            return json.dumps({"success": False, "msg": "Account not marked for deletion!"})
        
        elif ok == 0:
            cur.execute(f"UPDATE UserInfo SET username = '{encode('@deleted')}' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserInfo SET userId = {abs(uid)} WHERE userId = {uid}")
            conn.commit()
            
            return json.dumps({"success": False, "msg": "Account deleted"})
    
    elif command[0] == "delete_user_completely":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: delete_user_completely [userId]\nThe account must be deleted already and admins will be able to wipe all data stored in the database."})
        
        uid = 0
        if not command[1].isdigit():
            return json.dumps({"success": False, "msg": "Only user id is accepted here!"})
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        username = ""
        cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
        t = cur.fetchall()
        if len(t) != 0:
            username = decode(t[0][0])
        
        if username != "@deleted":
            return json.dumps({"success": False, "msg": "Account not deleted yet!"})
        
        elif username == "@deleted":
            uid = abs(uid)
            cur.execute(f"DELETE FROM CheckIn WHERE userId = {uid}")
            cur.execute(f"DELETE FROM UserSettings WHERE userId = {uid}")
            cur.execute(f"DELETE FROM UserNameTag WHERE userId = {uid}")
            cur.execute(f"DELETE FROM QuestionList WHERE userId = {uid}")
            cur.execute(f"DELETE FROM Privilege WHERE userId = {uid}")
            cur.execute(f"DELETE FROM Book WHERE userId = {uid}")
            cur.execute(f"DELETE FROM BookData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeData WHERE userId = {uid}")
            cur.execute(f"DELETE FROM ChallengeRecord WHERE userId = {uid}")
            cur.execute(f"DELETE FROM StatusUpdate WHERE userId = {uid}")
            cur.execute(f"DELETE FROM GroupMember WHERE userId = {uid}")
            cur.execute(f"DELETE FROM GroupSync WHERE userId = {uid}")
            cur.execute(f"DELETE FROM Discovery WHERE publisherId = {uid}")
            cur.execute(f"DELETE FROM IDInfo WHERE userId = {uid}")
            cur.execute(f"DELETE FROM UserSessionHistory WHERE userId = {uid}")
            conn.commit()

            return json.dumps({"success": False, "msg": "Account data wiped!"})
    
    elif command[0] == 'mute':
        if len(command) != 3:
            return json.dumps({"success": False, "msg": "Usage: mute [userId] [duration]\nMute [userId] for [duration] days\nTo mute forever, set [duration] to -1"})

        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if checkBanned(uid):
            return json.dumps({"success": False, "msg": "User has been banned!"})

        value = int(command[2])

        if uid == userId:
            return json.dumps({"success": False, "msg": "You cannot mute yourself!"})

        if value != -1:
            value = int(time.time()) + 86400 * value

        cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = 'mute'")
        if len(cur.fetchall()) == 0:
            cur.execute(f"INSERT INTO Privilege VALUES ({uid}, 'mute', '{value}')")
        else:
            cur.execute(f"UPDATE Privilege SET value = '{value}' WHERE userId = {uid} AND item = 'mute'")
        conn.commit()

        return json.dumps({"success": True, "msg": "User muted"})
    
    elif command[0] == "unmute":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: unmute [userId]\nUnmute [userId]"})
        
        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if checkBanned(uid):
            return json.dumps({"success": False, "msg": "User has been banned!"})

        cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = 'mute'")
        if len(cur.fetchall()) != 0:
            cur.execute(f"DELETE FROM Privilege WHERE userId = {uid} AND item = 'mute'")
            conn.commit()
            return json.dumps({"success": True, "msg": "User unmuted!"})
        else:
            return json.dumps({"success": False, "msg": "User not muted!"})

    elif command[0] == "set_privilege":
        if len(command) != 4:
            return json.dumps({"success": False, "msg": "Usage: set_privilege [userId] [item] [value]\nAdd [item] privilege for user [userId] ([item] can be question_limit)\nIf privilege exists, then update it"})

        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if checkBanned(uid):
            return json.dumps({"success": False, "msg": "User has been banned!"})

        item = command[2]
        value = int(command[3])

        if not item in ['question_limit', 'book_limit', 'allow_group_creation', 'group_member_limit']:
            return json.dumps({"success": False, "msg": f"Unknown privilege item: {item}. Acceptable item list: question_limit"})

        cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = '{item}'")
        if len(cur.fetchall()) == 0:
            cur.execute(f"INSERT INTO Privilege VALUES ({uid}, '{item}', {value})")
        else:
            cur.execute(f"UPDATE Privilege SET value = {value} WHERE userId = {uid} AND item = '{item}'")
        conn.commit()

        return json.dumps({"success": True, "msg": "Privilege set"})
    
    elif command[0] == "remove_privilege":
        if len(command) != 3:
            return json.dumps({"success": False, "msg": "Usage: remove_privilege [userId] [item]\nDelete [item] privilege from user [userId]"})

        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if checkBanned(uid):
            return json.dumps({"success": False, "msg": "User has been banned!"})

        item = command[2]

        if not item in ['question_limit', 'book_limit', 'allow_group_creation', 'group_member_limit']:
            return json.dumps({"success": False, "msg": f"Unknown privilege item: {item}. Acceptable item list: question_limit"})

        cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = '{item}'")
        if len(cur.fetchall()) != 0:
            cur.execute(f"DELETE FROM Privilege WHERE userId = {uid} AND item = '{item}'")
            conn.commit()
            return json.dumps({"success": True, "msg": "Privilege removed for this user"})
        else:
            return json.dumps({"success": False, "msg": "This user doesn't have this privilege!"})

    elif command[0] == "set_name_tag":
        if len(command) != 4:
            return json.dumps({"success": False, "msg": "Usage: set_name_tag [userId] [tag] [tag type]"})

        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if checkBanned(uid):
            return json.dumps({"success": False, "msg": "User has been banned!"})
            
        tag = encode(command[2])
        tagtype = command[3]

        if not tagtype.isalnum():
            return json.dumps({"success": False, "msg": "Invalid tag type!"})
        
        cur.execute(f"SELECT * FROM UserNameTag WHERE userId = {uid}")
        t = cur.fetchall()
        if len(t) == 0:
            if len(tag) > 32:
                return json.dumps({"success": False, "msg": "Tag too long!"})
            cur.execute(f"INSERT INTO UserNameTag VALUES ({uid}, '{tag}', '{tagtype}')")
        else:
            cur.execute(f"UPDATE UserNameTag SET tag = '{tag}' WHERE userId = {uid}")
            cur.execute(f"UPDATE UserNameTag SET tagtype = '{tagtype}' WHERE userId = {uid}")
        conn.commit()

        return json.dumps({"success": True, "msg": f"Added {tagtype} nametag for user {uid}"})

    elif command[0] == "remove_name_tag":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: remove_name_tag [userId]"})

        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid == 0:
            return json.dumps({"success": False, "msg": "Invalid user id!"})
        
        if checkBanned(uid):
            return json.dumps({"success": False, "msg": "User has been banned!"})

        cur.execute(f"SELECT * FROM UserNameTag WHERE userId = {uid}")
        t = cur.fetchall()
        if len(t) == 0:
            return json.dumps({"success": False, "msg": "User does not have a name tag!"})
        else:
            cur.execute(f"DELETE FROM UserNameTag WHERE userId = {uid}")
        conn.commit()

        return json.dumps({"success": True, "msg": f"Removed nametag from user {uid}"})


    elif command[0] == "ban":
        if len(command) < 3:
            return json.dumps({"success": False, "msg": "Usage: ban [userId] [reason]\nBan account"})
        
        uid = 0
        if not command[1].isdigit():
            uid = usernameToUid(encode(command[1]))
        else:
            uid = int(command[1])
        if uid <= 0:
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

        reason = encode(" ".join(command[2:]))
        cur.execute(f"UPDATE UserInfo SET userId = {-uid} WHERE userId = {uid}")
        cur.execute(f"INSERT INTO BanReason VALUES ({uid}, '{reason}')")
        conn.commit()

        return json.dumps({"success": False, "msg": f"Banned user {uid}"})

    elif command[0] == "unban":
        if len(command) != 2:
            return json.dumps({"success": False, "msg": "Usage: unban [userId]\nUnban account"})
        
        uid = 0
        if not command[1].isdigit():
            uid = abs(usernameToUid(encode(command[1])))
        else:
            uid = int(command[1])
        if uid == 0:
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
                cur.execute(f"DELETE FROM BanReason WHERE userId = {uid}")
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
        
        return json.dumps({"success": True, "msg": f"Total user: {tot}\nActive user: {cnt - deled}\nBanned / Banned & Deleted user: {banned}\nDisabled (Pending deletion) user: {marked_deletion}\nDeleted user: {deled}"})

    elif command[0] == "restart":
        if os.path.exists("/tmp/MyMemoLastManualRestart"):
            lst = int(open("/tmp/MyMemoLastManualRestart","r").read())
            if int(time.time()) - lst <= 300:
                return json.dumps({"success": False, "msg": "Only one restart in each 5 minutes is allowed!"})
        
        open("/tmp/MyMemoLastManualRestart","w").write(str(int(time.time())))

        threading.Thread(target=restart).start()
        return json.dumps({"success": True, "msg": "Server restarting..."})

    else:
        return json.dumps({"success": False, "msg": "Unknown command"})