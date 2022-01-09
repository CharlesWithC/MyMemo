# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

from fastapi import Request
from captcha.image import ImageCaptcha
import json, base64, uuid
from io import BytesIO

from app import app
from db import newconn
from functions import *

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
    return {"success": True, "version": "v5.6.9"}

@app.get("/api/captcha")
async def apiGetCaptcha(request: Request):
    s = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    rs = ""
    for _ in range(6):
        rs = rs + random.choice(s)
    
    img = ImageCaptcha()
    image = img.generate_image(rs)
    rgbl = [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
    image = img.create_noise_dots(image, tuple(rgbl))
    for _ in range(3):
        rgbl=  [random.randint(0,255), random.randint(0,255), random.randint(0,255)]
        image = img.create_noise_curve(image, tuple(rgbl))

    f = BytesIO()
    image.save(f, format="jpeg")
    image_data = f.getvalue()
    f.close()

    b64 = base64.b64encode(image_data)
    
    conn = newconn()
    cur = conn.cursor()
    token = uuid.uuid4()
    cur.execute(f"INSERT INTO Captcha VALUES ('{token}', '{rs}', {int(time.time() + 30)})")
    conn.commit()

    return {"success": True, "captchaToken": token, "captchaBase64": b64}