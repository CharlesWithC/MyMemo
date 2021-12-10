# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request
import json

from app import app

import apis.user
import apis.admin
import apis.question.main
import apis.book.main
import apis.group
import apis.share
import apis.data
import apis.discovery

@app.post("/api/ping")
async def ping(request: Request):
    form = await request.form()
    msg = form["msg"]
    return {"success": True, "msg": msg}