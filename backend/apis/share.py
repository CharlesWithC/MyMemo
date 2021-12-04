# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort
import os, sys, time
import json

from app import app, config
import db
from functions import *
import sessions

import MySQLdb
import sqlite3
conn = None

def updateconn():
    global conn
    if config.database == "mysql":
        conn = MySQLdb.connect(host = app.config["MYSQL_HOST"], user = app.config["MYSQL_USER"], \
            passwd = app.config["MYSQL_PASSWORD"], db = app.config["MYSQL_DB"])
    elif config.database == "sqlite":
        conn = sqlite3.connect("database.db", check_same_thread = False)
    
updateconn()

##########
# Share API

@app.route("/api/share", methods = ['POST'])
def apiShareBook():
    updateconn()
    cur = conn.cursor()
    if not "userId" in request.form.keys() or not "token" in request.form.keys() or "userId" in request.form.keys() and (not request.form["userId"].isdigit() or int(request.form["userId"]) < 0):
        abort(401)

    userId = int(request.form["userId"])
    token = request.form["token"]
    if not validateToken(userId, token):
        abort(401)
    
    op = request.form["operation"]

    if op == "list":
        ret = []
        i2n = {}
        cur.execute(f"SELECT bookId, shareCode, importCount, createTS FROM BookShare WHERE userId = {userId} AND shareType = 0")
        d = cur.fetchall()
        for dd in d:
            name = ""
            if dd[0] in i2n.keys():
                name = i2n[dd[0]]
            else:
                cur.execute(f"SELECT name FROM Book WHERE bookId = {dd[0]}")
                t = cur.fetchall()
                if len(t) == 0:
                    continue
                name = decode(t[0][0])
                i2n[dd[0]] = name
            
            ret.append({"bookId": dd[0], "name": name, "shareCode": "!" + dd[1], "importCount": dd[2], "timestamp": dd[3]})
        
        del i2n

        return json.dumps(ret)

    elif op == "create":
        bookId = int(request.form["bookId"])

        cur.execute(f"SELECT * FROM Book WHERE userId = {userId} AND bookId = {bookId}")
        if len(cur.fetchall()) == 0:
            return json.dumps({"success": False, "msg": "Book not found!"})
        
        cur.execute(f"SELECT shareCode FROM BookShare WHERE userId = {userId} AND bookId = {bookId} AND shareType = 0")
        t = cur.fetchall()
        if len(t) >= 20:
            return json.dumps({"success": False, "msg": "You can create at most 20 shares for one book!"})
        else:
            shareCode = genCode(8)
            cur.execute(f"SELECT shareCode FROM BookShare WHERE shareCode = '{shareCode}'")
            if len(cur.fetchall()) != 0: # conflict
                for _ in range(30):
                    shareCode = genCode(8)
                    cur.execute(f"SELECT shareCode FROM Book WHERE shareCode = '{shareCode}'")
                    if len(cur.fetchall()) == 0:
                        break
                cur.execute(f"SELECT shareCode FROM Book WHERE shareCode = '{shareCode}'")
                if len(cur.fetchall()) != 0:
                    return json.dumps({"success": False, "msg": "Unable to generate an unique share code..."})
                    
            cur.execute(f"INSERT INTO BookShare VALUES ({userId}, {bookId}, '{shareCode}', 0, {int(time.time())}, 0)")
            conn.commit()

            return json.dumps({"success": True, "msg": "A new book share has been created!", "shareCode": "!" + shareCode})

    elif op == "remove":
        code = request.form["shareCode"]
        code = code.replace("!","").replace("@","")

        if not code.isalnum():
            return json.dumps({"success": False, "msg": "Invalid share code!"})

        cur.execute(f"SELECT bookId FROM BookShare WHERE userId = {userId} AND shareType = 0 AND shareCode = '{code}'")
        t = cur.fetchall()
        if len(t) == 0:
            return json.dumps({"success": False, "msg": "Invalid share code!"})
        else:
            cur.execute(f"DELETE FROM BookShare WHERE userId = {userId} AND bookId = {t[0][0]} AND shareCode = '{code}'")
            conn.commit()
            return json.dumps({"success": True, "msg": "Book unshared!"})