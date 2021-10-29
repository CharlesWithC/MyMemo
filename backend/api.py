# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort, send_file
import os, sys, datetime, time, math
import random, uuid
import json
import validators
import sqlite3
import pandas as pd

from app import app, config
from functions import *
import sessions

import apis.user
import apis.admin
import apis.word.main
import apis.wordbook.main
import apis.group
import apis.data

conn = sqlite3.connect("database.db", check_same_thread = False)

@app.route("/api/ping", methods = ['POST'])
def ping():
    msg = request.form["msg"]
    return json.dumps({"success": True, "msg": msg})