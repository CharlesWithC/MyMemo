# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request
import json

from app import app

import apis.user.main
import apis.question.main
import apis.book.main
import apis.discovery.main
import apis.group
import apis.share
import apis.data
import apis.admin

@app.get("/api/version")
async def apiGetVersion(request: Request):
    ip = request.client.host
    return {"success": True, "version": "v5.6.3"}