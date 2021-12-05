# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from flask import request, abort, send_file
import os, sys, datetime, time, math
import random, uuid
import json
import validators
import pandas as pd

from app import app, config
from db import newconn
from functions import *
import sessions

import apis.user
import apis.admin
import apis.question.main
import apis.book.main
import apis.group
import apis.share
import apis.data
import apis.discovery

@app.route("/api/ping", methods = ['POST'])
def ping():
    msg = request.form["msg"]
    return json.dumps({"success": True, "msg": msg})