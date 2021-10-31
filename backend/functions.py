# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import bcrypt
import random
import base64
import sqlite3

import sessions
import time

conn = sqlite3.connect("database.db", check_same_thread = False)

def hashpwd(password):
    return bcrypt.hashpw(password.encode(),bcrypt.gensalt(12)).decode()

def checkpwd(password, hsh):
    return bcrypt.checkpw(password.encode(),hsh.encode())

st="abcdefghjkmnpqrstuvwxy3456789ABCDEFGHJKMNPQRSTUVWXY"
def genCode(length = 8):
    ret = ""
    for _ in range(length):
        ret += st[random.randint(0,len(st)-1)]
    return ret

def encode(s):
    return base64.b64encode(s.encode()).decode()

def decode(s):
    return base64.b64decode(s.encode()).decode()
    
def validateToken(userId, token):
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0 or d[0][0] == "@deleted":
        return False
    
    return sessions.validateToken(userId, token)

def getWordsInWordBook(userId, wordBookId, statusRequirement):
    cur = conn.cursor()
    cur.execute(f"SELECT wordId FROM WordBookData WHERE wordBookId = {wordBookId} AND userId = {userId}")
    wordbook = cur.fetchall()
    cur.execute(f"SELECT wordId, word, translation, status FROM WordList WHERE ({statusRequirement}) AND userId = {userId}")
    words = cur.fetchall()
    d = []
    for word in words:
        if (word[0],) in wordbook:
            d.append(word)
    return d
    
def updateWordStatus(userId, wordId, status):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE wordId = {wordId} AND userId = {userId}")
    d = cur.fetchall()
    wordUpdateId = 0
    if len(d) != 0:
        wordUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({userId},{wordId},{wordUpdateId},{status},{int(time.time())})")
    conn.commit()