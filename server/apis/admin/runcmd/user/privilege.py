# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

# Admin commands: User Limit

import time

from db import newconn
from functions import *

def set_privilege(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 4:
        return {"success": False, "msg": "Usage: set_privilege [userId] [item] [value]\nAdd [item] privilege for user [userId] ([item] can be question_limit)\nIf privilege exists, then update it"}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}

    item = command[2]
    value = int(command[3])

    if not item in ['question_limit', 'book_limit', 'allow_group_creation', 'group_member_limit']:
        return {"success": False, "msg": f"Unknown privilege item: {item}. Acceptable item list: question_limit, book_limit, allow_group_creation, group_member_limit"}

    cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = '{item}'")
    if len(cur.fetchall()) == 0:
        cur.execute(f"INSERT INTO Privilege VALUES ({uid}, '{item}', {value})")
    else:
        cur.execute(f"UPDATE Privilege SET value = {value} WHERE userId = {uid} AND item = '{item}'")
    conn.commit()

    return {"success": True, "msg": "Privilege set"}

def remove_privilege(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 3:
        return {"success": False, "msg": "Usage: remove_privilege [userId] [item]\nDelete [item] privilege from user [userId]"}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}

    item = command[2]

    if not item in ['question_limit', 'book_limit', 'allow_group_creation', 'group_member_limit']:
        return {"success": False, "msg": f"Unknown privilege item: {item}. Acceptable item list: question_limit"}

    cur.execute(f"SELECT * FROM Privilege WHERE userId = {uid} AND item = '{item}'")
    if len(cur.fetchall()) != 0:
        cur.execute(f"DELETE FROM Privilege WHERE userId = {uid} AND item = '{item}'")
        conn.commit()
        return {"success": True, "msg": "Privilege removed for this user"}
    else:
        return {"success": False, "msg": "This user doesn't have this privilege!"}

def set_name_tag(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 4:
        return {"success": False, "msg": "Usage: set_name_tag [userId] [tag] [tag color]"}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}
        
    tag = encode(command[2])
    tagtype = command[3]

    if not tagtype.isalnum():
        return {"success": False, "msg": "Invalid tag color!"}
    
    cur.execute(f"SELECT * FROM UserNameTag WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) == 0:
        if len(tag) > 32:
            return {"success": False, "msg": "Tag too long!"}
        cur.execute(f"INSERT INTO UserNameTag VALUES ({uid}, '{tag}', '{tagtype}')")
    else:
        cur.execute(f"UPDATE UserNameTag SET tag = '{tag}' WHERE userId = {uid}")
        cur.execute(f"UPDATE UserNameTag SET tagtype = '{tagtype}' WHERE userId = {uid}")
    conn.commit()

    return {"success": True, "msg": f"Added {tagtype} nametag for user {uid}"}

def remove_name_tag(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 2:
        return {"success": False, "msg": "Usage: remove_name_tag [userId]"}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}

    cur.execute(f"SELECT * FROM UserNameTag WHERE userId = {uid}")
    t = cur.fetchall()
    if len(t) == 0:
        return {"success": False, "msg": "User does not have a name tag!"}
    else:
        cur.execute(f"DELETE FROM UserNameTag WHERE userId = {uid}")
    conn.commit()

    return {"success": True, "msg": f"Removed nametag from user {uid}"}

def add_admin(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 2:
        return {"success": False, "msg": "Usage: add_admin [userId]\nAdd [userId] to administrator list."}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}

    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {uid}")
    if len(cur.fetchall()) == 0:
        cur.execute(f"INSERT INTO AdminList VALUES ({uid})")
        conn.commit()
        return {"success": True, "msg": f"Added user {command[1]} to administrator list!"}
    
    else:
        return {"success": True, "msg": f"User {command[1]} is already an administrator!"}

def remove_admin(userId, command):
    conn = newconn()
    cur = conn.cursor()
    if len(command) != 2:
        return {"success": False, "msg": "Usage: remove_admin [userId]\nRemove [userId] from administrator list."}

    uid = 0
    if not command[1].isdigit():
        uid = usernameToUid(encode(command[1]))
    else:
        uid = int(command[1])
    if uid == 0:
        return {"success": False, "msg": "Invalid user id!"}
    
    if checkBanned(uid):
        return {"success": False, "msg": "User has been banned!"}

    cur.execute(f"SELECT userId FROM AdminList WHERE userId = {uid}")
    if len(cur.fetchall()) != 0:
        cur.execute(f"DELETE FROM AdminList WHERE userId = {uid}")
        conn.commit()
        return {"success": True, "msg": f"Removed user {command[1]} from administrator list!"}
    
    else:
        return {"success": True, "msg": f"User {command[1]} is not an administrator!"}