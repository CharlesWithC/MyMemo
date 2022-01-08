# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import bcrypt
import random
import base64
import time
import re
import math

from app import app, config
from db import newconn
import sessions

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

def encode(s, removeHTMLTag = True):
    try:
        s = s.replace("\n","  \n")
        if removeHTMLTag:
            s = re.sub("\\<.*?\\>", "<HTML_REMOVED>", s)
        s = s.replace("\\n","<n>")
        s = s.replace("\n","<br>")
        return base64.b64encode(s.encode()).decode()
    except:
        print(f"Unable to encode {s}")
        return ""

def decode(s):
    try:
        return base64.b64decode(s.encode()).decode().replace("<br>","\n").replace("<n>","\\n")
    except:
        print(f"Unable to decode {s}")
        return ""

def checkBanned(userId):
    conn = newconn()
    cur = conn.cursor()
    userId = abs(userId)
    cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {userId}")
    if len(cur.fetchall()) > 0:
        
        return False
    else:
        cur.execute(f"SELECT userId FROM UserInfo WHERE userId = {-userId}")
        if len(cur.fetchall()) > 0:
            
            return True
        else:
            
            return False
    
def validateToken(userId, token):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT username FROM UserInfo WHERE userId = {userId}")
    d = cur.fetchall()
    
    if len(d) == 0 or decode(d[0][0]) == "@deleted":
        
        return False
    
    if checkBanned(abs(userId)):
        
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

# def getBookData(userId, bookId):
#     conn = newconn()
#     cur = conn.cursor()
#     ret = []
#     cur.execute(f"SELECT questions FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
#     t = cur.fetchall()
#     for tt in t:
#         d = b62decode_batch(tt[0])
#         for dd in d:
#             ret.append(dd)
#     ret = list(set(ret)) # unique
#     ret.sort()
#     conn.close()    
#     return ret

# def getBookId(userId, questionId):
#     conn = newconn()
#     cur = conn.cursor()
#     ret = []
#     cur.execute(f"SELECT questions, bookId FROM BookData WHERE userId = {userId}")
#     t = cur.fetchall()
#     for tt in t:
#         d = b62decode_batch(tt[0])
#         for dd in d:
#             if dd == questionId:
#                 ret.append(tt[1])
#     ret = list(set(ret)) # unique
#     ret.sort()
#     conn.close()    
#     return ret

# def appendBookData(userId, bookId, questionId):
#     conn = newconn()
#     cur = conn.cursor()
#     toadd = b62encode(questionId) + "|"
#     cur.execute(f"SELECT questions, page FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
#     t = cur.fetchall()

#     # check existence
#     for tt in t:
#         data = tt[0]
#         if toadd in data:
#             conn.close()
#             return False
    
#     # append
#     success = False
#     for tt in t:
#         data = tt[0]
#         page = tt[1]
#         if len(data) + len(toadd) < 256:
#             cur.execute(f"UPDATE BookData SET questions = '{data + toadd}' WHERE userId = {userId} AND bookId = {bookId} AND page = {page}")
#             success = True
#             break
#     if not success:
#         cur.execute(f"INSERT INTO BookData VALUES ({userId}, {bookId}, '{toadd}', {len(t) + 1})")
#     conn.commit()
#     conn.close()    
#     return True

# def removeBookData(userId, bookId, questionId):
#     for _ in range(3):
#         try:
#             conn = newconn()
#             cur = conn.cursor()
#             toremove = b62encode(questionId) + "|"
#             t = None
#             if bookId != -1:
#                 cur.execute(f"SELECT questions, page FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
#             elif bookId == -1:
#                 cur.execute(f"SELECT questions, page, bookId FROM BookData WHERE userId = {userId}")
#             t = cur.fetchall()
#             for tt in t:
#                 questions = tt[0]
#                 page = tt[1]
#                 if toremove in questions:
#                     questions = questions.replace(toremove, "")
#                     if bookId != -1:
#                         cur.execute(f"UPDATE BookData SET questions = '{questions}' WHERE userId = {userId} AND bookId = {bookId} AND page = {page}")
#                     elif bookId == -1:
#                         cur.execute(f"UPDATE BookData SET questions = '{questions}' WHERE userId = {userId} AND bookId = {tt[2]} AND page = {page}")
                    
#                     if bookId != -1:
#                         cur.execute(f"SELECT memorizedTimestamp FROM QuestionList WHERE userId = {userId} AND questionId = {questionId}")
#                         p = cur.fetchall()
#                         if len(p) > 0 and p[0][0] != 0:
#                             cur.execute(f"UPDATE Book SET progress = progress - 1 WHERE userId = {userId} AND bookId = {bookId}")
#                     conn.commit()
#                     conn.close()
                    
#                     return True
                    
#             conn.commit()
#             conn.close()
            
#             return False

#         except:
#             conn.close()
#             import traceback
#             traceback.print_exc()
#             time.sleep(3)
#             pass
#     return False

# def getQuestionsInBook(userId, bookId, statusRequirement):
#     if statusRequirement == "":
#         statusRequirement = "status >= 1"
#     conn = newconn()
#     cur = conn.cursor()
#     book = getBookData(userId, bookId)
#     cur.execute(f"SELECT questionId, question, answer, status FROM QuestionList WHERE ({statusRequirement}) AND userId = {userId}")
#     questions = cur.fetchall()
#     d = []
#     if bookId > 0:
#         for question in questions:
#             if question[0] in book:
#                 d.append(question)
#     else:
#         d = questions
#     conn.commit()
#     conn.close()
    
#     return d

def getBookData(userId, bookId):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT questionId FROM BookData WHERE userId = {userId} AND bookId = {bookId}")
    t = cur.fetchall()
    ret = []
    for tt in t:
        ret.append(tt[0])
    return ret

def getBookId(userId, questionId):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT bookId FROM BookData WHERE userId = {userId} AND questionId = {questionId}")
    t = cur.fetchall()
    ret = []
    for tt in t:
        ret.append(tt[0])
    return ret
    
def getQuestionsInBook(userId, bookId, statusRequirement):
    if statusRequirement == "":
        statusRequirement = "status >= 1"
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT questionId FROM BookData WHERE bookId = {bookId}")
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
    conn.commit()
    conn.close()
    
    return d

def updateQuestionStatus(userId, questionId, status):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM StatusUpdate WHERE questionId = {questionId} AND userId = {userId}")
    d = cur.fetchall()
    questionUpdateId = 0
    if len(d) != 0:
        questionUpdateId = d[0][0]
    cur.execute(f"INSERT INTO StatusUpdate VALUES ({userId},{questionId},{questionUpdateId},{status},{int(time.time())})")
    conn.commit()
    conn.close()    
    
def getQuestionCount(userId):
    conn = newconn()
    cur = conn.cursor()
    q = 0
    cur.execute(f"SELECT COUNT(*) FROM QuestionList WHERE userId = {userId}")
    d = cur.fetchall()
    if len(d) > 0:
        q = d[0][0]
    conn.close()    
    return q

def usernameToUid(username):
    conn = newconn()
    cur = conn.cursor()
    cur.execute(f"SELECT userId FROM UserInfo WHERE username = '{username}'")
    t = cur.fetchall()
    conn.close()    
    if len(t) > 0:
        return t[0][0]
    else:
        return 0

# Allow [ip] to do at most [maxop] requests on [endpoint] within [timeout] seconds
# Note that userid can also represent ip
def OPLimit(ip, endpoint, maxop = 5, timeout = 300):
    conn = newconn()
    cur = conn.cursor()

    ip = str(ip)

    ip = encode(ip)
    cur.execute(f"SELECT count, last FROM OPLimit WHERE ip = '{ip}' AND endpoint = '{endpoint}'")
    t = cur.fetchall()
    if len(t) == 0:
        cur.execute(f"INSERT INTO OPLimit VALUES ('{ip}', '{endpoint}', 1, {int(time.time())})")
        conn.commit()
        return False

    count = t[0][0]
    last = t[0][1]
    if last < time.time() - timeout:
        cur.execute(f"DELETE FROM OPLimit WHERE ip = '{ip}' AND endpoint = '{endpoint}'")
        cur.execute(f"INSERT INTO OPLimit VALUES ('{ip}', '{endpoint}', 1, {int(time.time())})")
        conn.commit()
        return False
    
    if count == maxop:
        return True
    
    cur.execute(f"UPDATE OPLimit SET count = count + 1 WHERE ip = '{ip}' AND endpoint = '{endpoint}'")
    cur.execute(f"UPDATE OPLimit SET last = '{int(time.time())}' WHERE ip = '{ip}' AND endpoint = '{endpoint}'")
    conn.commit()

    return False

def validateCaptcha(captchaToken, captchaAnswer):
    conn = newconn()
    cur = conn.cursor()
        
    cur.execute(f"DELETE FROM Captcha WHERE expire < {int(time.time())}")
    conn.commit()
    
    if not captchaToken.replace("-", "").isalnum():
        return {"success": False, "captcha": True, "msg": "Invalid captcha token!"}
    cur.execute(f"SELECT answer, expire FROM Captcha WHERE token = '{captchaToken}'")
    t = cur.fetchall()
    
    if len(t) == 0 or t[0][1] < int(time.time()):
        return {"success": False, "captcha": True, "msg": "Captcha expired!"}

    cur.execute(f"DELETE FROM Captcha WHERE token = '{captchaToken}'")
    conn.commit()
    
    if t[0][0].lower() != captchaAnswer.lower():
        return {"success": False, "captcha": True, "msg": "Incorrect captcha!"}

    return True
from datetime import date

Months = {0:31, 1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}

def IsLeapYear(year):
    if year % 4 == 0:
        if year % 100 == 0:
            if year % 400 == 0:
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def CalculateAge(timestamp, humanReadable = True):
    year, month, day = 0, 0, 0
    
    try:
        date1 = date.fromtimestamp(timestamp)
        year1, mon1, day1 = date1.year, date1.month, date1.day
        date2 = date.today()
        year2, mon2, day2 = date2.year, date2.month, date2.day
        totalDays = (date2 - date1).days

        if int(year1) == int(year2):
            month = totalDays / 30
            day = totalDays % 30
            year = 0
        else:
            year = totalDays / 365
            month = (totalDays % 365) / 30
            if IsLeapYear(int(year1)):
                Months[2] = 29
            if int(day2) >= int(day1):
                day = int(day2) - int(day1)
            elif int(mon2) == 2 and (IsLeapYear(int(year2)) or (not IsLeapYear(int(year2)))):
                year = year - 1
                month = 11
                prevMonth = Months[int(mon2) - 1]
                days = prevMonth - int(day1) + int(day2)
                day = days
            else:
                prevMonth = Months[int(mon2) - 1]
                days = prevMonth - int(day1) + int(day2)
                day = days
        
        year, month, day = int(year), int(month), int(day)
    
    except:
        if humanReadable:
            day = math.ceil((time.time() - timestamp) / 86400)
        
    if humanReadable:
        year_s = "s"
        if year <= 1:
            year_s = ""
        month_s = "s"
        if month <= 1:
            month_s = ""
        day_s = "s"
        if day <= 1:
            day_s = ""
        if year > 0:
            return f"{year} year{year_s} {month} month{month_s} {day} day{day_s}"
        elif month > 0:
            return f"{month} month{month_s} {day} day{day_s}"
        elif day > 0:
            return f"{day} day{day_s}"
        else:
            return "1 day"
    else:
        return (year, month, day)