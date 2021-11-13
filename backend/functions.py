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

def getQuestionsInBook(userId, bookId, statusRequirement):
    cur = conn.cursor()
    cur.execute(f"SELECT questionId FROM BookData WHERE bookId = {bookId} AND userId = {userId}")
    book = cur.fetchall()
    cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE ({statusRequirement}) AND userId = {userId}")
    questions = cur.fetchall()
    d = []
    if bookId > 0:
        for question in questions:
            if (question[0],) in book:
                d.append(question)
    else:
        d = questions
    return d
    
def updateQuestionStatus(userId, questionId, status):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    questionUpdateId = 0
    if len(d) != 0:
        questionUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({userId},{questionId},{questionUpdateId},{status},{int(time.time())})")
    conn.commit()
    
def getQuestionCount(userId):
    cur = conn.cursor()
    q = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) > 0:
        q = d[0][0]
    return q