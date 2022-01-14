# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import time
import uuid
import validators

from db import newconn
from functions import *
from emailop import sendVerification

def create_user(userId, command):
    if len(command) != 4:
        return {"success": False, "msg": f"Usage: create_user [username] [email] [password]\nCreate a user by admin, user will be shown as invited by this admin"}
    
    username = command[1]
    email = command[2]
    password = command[3]
    inviter = userId # inviter is admin

    if " " in username or "(" in username or ")" in username or "[" in username or "]" in username or "{" in username or "}" in username \
        or "<" in username or ">" in username \
            or "!" in username or "@" in username or "'" in username or '"' in username or "/" in username or "\\" in username :
        return {"success": False, "msg": "Username must not contain: spaces, ( ) [ ] { } < > ! @ ' \" / \\"}

    username = encode(username)
    if validators.email(email) != True:
        return {"success": False, "msg": "Invalid email!"}

    cur.execute(f"DELETE FROM UserPending WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT username, email FROM UserPending")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if decode(tt[1]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}
            
    cur.execute(f"DELETE FROM PendingEmailChange WHERE expire < {int(time.time())}")
    conn.commit()
    cur.execute(f"SELECT email FROM PendingEmailChange")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}
        elif tt[0].startswith("!") and decode(tt[0].lower()[1:]) == email.lower():
            return {"success": False, "msg": "The previous owner of this email has updated their email within 7 days so this email address is reserved for 7 days!"}

    cur.execute(f"SELECT username, email FROM UserInfo")
    t = cur.fetchall()
    for tt in t:
        if decode(tt[0]).lower() == decode(username).lower():
            return {"success": False, "msg": "Username has been occupied!"}
        if decode(tt[1]).lower() == email.lower():
            return {"success": False, "msg": "Email has already been registered!"}

    password = hashpwd(password)
    
    token = str(uuid.uuid4())
    background_tasks.add_task(sendVerification, email, decode(username), "Account activation", \
        f"Welcome {decode(username)}! Please verify your email to activate your account!", "3 hours", \
            "https://memo.charles14.xyz/user/activate?token="+token)
            
    puserId = 1
    try:
        cur.execute(f"SELECT nextId FROM IDInfo WHERE type = 0")
        t = cur.fetchall()
        if len(t) > 0:
            puserId = t[0][0]
        cur.execute(f"UPDATE IDInfo SET nextId = {puserId + 1} WHERE type = 0")

        cur.execute(f"INSERT INTO UserPending VALUES ({puserId}, '{username}', '{encode(email)}', '{encode(password)}', {inviter}, '{token}', {int(time.time() + 3600 * 3)})")
        conn.commit()

        return {"success": True, "msg": f"User registered but pending email verification!"}
    except:
        sessions.errcnt += 1
        return {"success": False, "msg": "Unknown error occured. Try again later..."}

def delete_pending(userId, command):
    if len(command) != 2:
        return {"success": False, "msg": "Usage: delete_pending [puserId]\nDelete a pending user"}

    puserId = command[1]

    if puserId.isdigit():
        cur.execute(f"SELECT * FROM UserPending WHERE puserId = {puserId}")
        if len(cur.fetchall()) == 0:
            cur.execute(f"SELECT puserId FROM UserPending WHERE username = '{encode(puserId)}'")
            t = cur.fetchall()
            if len(t) == 0:
                return {"success": False, "msg": "User not found!"}
            else:
                puserId = t[0][0]
        else:
            puserId = int(puserId)
    else:
        cur.execute(f"SELECT puserId FROM UserPending WHERE username = '{encode(puserId)}'")
        t = cur.fetchall()
        if len(t) == 0:
            return {"success": False, "msg": "User not found!"}
        else:
            puserId = t[0][0]
        
    cur.execute(f"DELETE FROM UserPending WHERE puserId = {puserId}")
    cur.execute(f"DELETE FROM UserPendingToken WHERE puserId = {puserId}")
    conn.commit()

    return {"success": True, "msg": "User deleted!"}            

def delete_user(userId, command):
    if len(command) != 2:
        return {"success": False, "msg": "Usage: delete_user [userId]\nThe account must be marked as deletion first, and admin will be able to bring the deletion schedule forward"}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
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
                return {"success": False, "msg": "Revoked account creation!"}

        return {"success": False, "msg": "Account not marked for deletion!"}
    
    elif ok == 0:
        cur.execute(f"UPDATE UserInfo SET username = '{encode('@deleted')}' WHERE userId = {uid}")
        cur.execute(f"UPDATE UserInfo SET email = '' WHERE userId = {uid}")
        cur.execute(f"UPDATE UserInfo SET password = '' WHERE userId = {uid}")
        cur.execute(f"UPDATE UserInfo SET userId = {abs(uid)} WHERE userId = {uid}")
        conn.commit()
        
        return {"success": True, "msg": "Account deleted"}

def wipe_user(userId, command):
    if len(command) != 2:
        return {"success": False, "msg": "Usage: wipe_user [userId]\nThe account must be deleted already and admins will be able to wipe all data stored in the database."}
    
    uid = 0
    if not command[1].isdigit():
        return {"success": False, "msg": "Only user id is accepted here!"}
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    username = ""
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) != 0:
        username = decode(t[0][0])
    
    if username != "@deleted":
        return {"success": False, "msg": "Account not deleted yet!"}
    
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

        return {"success": True, "msg": "Account data wiped!"}