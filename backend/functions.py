# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import bcrypt
import random
import base64
import time

from app import app, config
import sessions

import MySQLdb
import sqlite3
conn = None

def updateconn():
    global conn
    if config.database == "mysql":
        if app.config["DB_ENABLED"]:
            conn = MySQLdb.connect(host = app.config["MYSQL_HOST"], user = app.config["MYSQL_USER"], \
                passwd = app.config["MYSQL_PASSWORD"], db = app.config["MYSQL_DB"])
    elif config.database == "sqlite":
        if app.config["DB_ENABLED"]:
            conn = sqlite3.connect("database.db", check_same_thread = False)

updateconn()


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
    try:
        return base64.b64encode(s.encode()).decode()
    except:
        print(f"Unable to encode {s}")
        return ""

def decode(s):
    try:
        return base64.b64decode(s.encode()).decode()
    except:
        print(f"Unable to decode {s}")
        return ""
    
def validateToken(userId, token):
    updateconn()
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) == 0 or decode(d[0][0]) == "@deleted":
        return False
    
    return sessions.validateToken(userId, token)

def b62encode(d):
    ret = ""
    l = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if d == 0:
        return l[0]
    while d:
        ret += l[d % 62]
        d //= 62
    return ret[::-1]

def b62decode(d):
    ret = 0
    l = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i in range(len(d)):
        ret += l.find(d[i]) * 62 ** (len(d) - i - 1)
    return ret

def b62encode_batch(d):
    ret = ""
    for dd in d:
        ret += b62encode(dd) + "|"
    return ret

def b62decode_batch(d):
    t = d.split("|")[:-1]
    ret = []
    for tt in t:
        ret.append(b62decode(tt))
    return ret

def getBookData(userId, bookId):
    updateconn()
    cur = conn.cursor()
    ret = []
    cur.execute(f"SELECT questions FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    t = cur.fetchall()
    for tt in t:
        d = b62decode_batch(tt[0])
        for dd in d:
            ret.append(dd)
    ret = list(set(ret)) # unique
    ret.sort()
    return ret

def getBookId(userId, questionId):
    updateconn()
    cur = conn.cursor()
    ret = []
    cur.execute(f"SELECT questions, bookId FROM BookData WHERE userId = {userId}")
    t = cur.fetchall()
    for tt in t:
        d = b62decode_batch(tt[0])
        for dd in d:
            if dd == questionId:
                ret.append(tt[1])
    ret = list(set(ret)) # unique
    ret.sort()
    return ret

def appendBookData(userId, bookId, questionId):
    updateconn()
    cur = conn.cursor()
    toadd = b62encode(questionId) + "|"
    cur.execute(f"SELECT questions, page FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    t = cur.fetchall()

    # check existence
    for tt in t:
        data = tt[0]
        if toadd in data:
            return False
    
    # append
    success = False
    for tt in t:
        data = tt[0]
        page = tt[1]
        if len(data) + len(toadd) < 409600:
            cur.execute(f"UPDATE BookData SET questions = '{data + toadd}' WHERE userId = {userId} AND bookId = {bookId} AND page = {page}")
            success = True
            break
    if not success:
        cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, '{toadd}', {len(t) + 1})")
    conn.commit()
    return True

def removeBookData(userId, bookId, questionId):
    updateconn()
    cur = conn.cursor()
    toremove = b62encode(questionId) + "|"
    t = None
    if bookId != -1:
        cur.execute(f"SELECT questions, page FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    elif bookId == -1:
        cur.execute(f"SELECT questions, page, bookId FROM BookData WHERE userId = {userId}")
    t = cur.fetchall()
    for tt in t:
        questions = tt[0]
        page = tt[1]
        if toremove in questions:
            questions = questions.replace(toremove, "")
            if bookId != -1:
                cur.execute(f"UPDATE BookData SET questions = '{questions}' WHERE userId = {userId} AND bookId = {bookId} AND page = {page}")
            elif bookId == -1:
                cur.execute(f"UPDATE BookData SET questions = '{questions}' WHERE userId = {userId} AND bookId = {tt[2]} AND page = {page}")
            conn.commit()
            return True
    return False

def getQuestionsInBook(userId, bookId, statusRequirement):
    if statusRequirement == "":
        statusRequirement = "status >= 1"
    updateconn()
    cur = conn.cursor()
    book = getBookData(userId, bookId)
    cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE ({statusRequirement}) AND userId = {userId}")
    questions = cur.fetchall()
    d = []
    if bookId > 0:
        for question in questions:
            if question[0] in book:
                d.append(question)
    else:
        d = questions
    return d
    
def updateQuestionStatus(userId, questionId, status):
    updateconn()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    questionUpdateId = 0
    if len(d) != 0:
        questionUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({userId},{questionId},{questionUpdateId},{status},{int(time.time())})")
    conn.commit()
    
def getQuestionCount(userId):
    updateconn()
    cur = conn.cursor()
    q = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) > 0:
        q = d[0][0]
    return q

def usernameToUid(username):
    updateconn()
    cur = conn.cursor()
    cur.execute(f"SELECT userId FROM UserInfo WHERE username = '{username}'")
    t = cur.fetchall()
    if len(t) > 0:
        return t[0][0]
    else:
        return 0