# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import sqlite3
import os, sys
import bcrypt
import json
import random


if os.path.exists("./database.db"):
    t = input("Are you sure to init the database? This will clear the old one if it exists! (Y/N)")
    if t.upper() != "Y":
        print("Aborted")
        sys.exit(0)
    else:
        os.remove("./database.db")

from functions import *

class Dict2Obj(object):
    def __init__(self, d):
        for key in d:
            if type(d[key]) is dict:
                data = Dict2Obj(d[key])
                setattr(self, key, data)
            else:
                setattr(self, key, d[key])

config = None
if os.path.exists("./config.json"):
    config_txt = open("./config.json","r").read()
    config = Dict2Obj(json.loads(config_txt))


conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

cur.execute(f"CREATE TABLE UserInfo (userId INT, username VARCHAR(64), email VARCHAR(128), password VARCHAR(256), inviter INT, inviteCode CHAR(5))")
# Allow only inviting registration mode to prevent abuse
cur.execute(f"CREATE TABLE UserEvent (userId INT, event VARCHAR(32), timestamp INT)")
# Available event: register, login, change_password, delete_account

# User should be allowed to delete their accounts
# When a user request to delete his account, his account will be marked as "Pending for deletion",
# and will be deleted in 14 days. 
# During the 14 days, user will be allowed to recover the account. (Like Discord)
# After the 14 days, all of the user's data will be wiped, including UserInfo, QuestionList, ChallengeData etc
# But his/her userId will persist forever, while it represents an empty account named "Deleted Account"

# If user id becomes a negative number, it means this user has been banned

defaultpwd = hashpwd(config.default_user_password)

cur.execute(f"INSERT INTO UserInfo VALUES (0,'default','None','{encode(defaultpwd)}',0,'{genCode(6)}')")
cur.execute(f"INSERT INTO UserEvent VALUES (0, 'register', 0)")
# Default user system's password is 123456
# Clear default account's password after setup (so it cannot be logged in)
# NOTE DO NOT DELETE THE DEFAULT ACCOUNT, keep it in the database record

cur.execute(f"CREATE TABLE Previlege (userId INT, item VARCHAR(32), value INT)")
# User previlege, such as question_limit, book_limit, allow_group_creation, group_member_limit

cur.execute(f"CREATE TABLE AdminList (userId INT)")
# Currently this admin list can only be edited from backend using database operations

cur.execute(f"CREATE TABLE QuestionList (userId INT, questionId INT, question VARCHAR(1024), answer VARCHAR(1024), status INT)")
# questionId is unique for each question, when the question is removed, its questionId will refer to null
# EXAMPLE: Book 1 has questionId 1,2 and Book 2 has questionId 3
# question and answer are encoded with base64 to prevent datalose
# status is a status code while 1 refers to Default, 2 refers to Tagged and 3 refers to removed
cur.execute(f"CREATE TABLE MyMemorized (userId INT, questionId INT)")

cur.execute(f"CREATE TABLE Book (userId INT, bookId INT, name VARCHAR(1024))")
cur.execute(f"CREATE TABLE BookData (userId INT, bookId INT, questionId INT)")
# When a new question is added, it belongs to no book
# A question can belong to many books
cur.execute(f"CREATE TABLE BookShare (userId INT, bookId INT, shareCode VARCHAR(8))")
cur.execute(f"CREATE TABLE BookProgress (userId INT, bookId INT, progress INT)")

cur.execute(f"CREATE TABLE GroupInfo (groupId INT, owner INT, name VARCHAR(256), description VARCHAR(1024), memberLimit INT, groupCode VARCHAR(8))")
cur.execute(f"CREATE TABLE GroupMember (groupId INT, userId INT, isEditor INT)")
cur.execute(f"CREATE TABLE GroupQuestion (groupId INT, groupQuestionId INT, question VARCHAR(1024), answer VARCHAR(1024))")
cur.execute(f"CREATE TABLE GroupSync (groupId INT, userId INT, questionIdOfUser INT, questionIdOfGroup INT)") # book id of user
cur.execute(f"CREATE TABLE GroupBind (groupId INT, userId INT, bookId INT)") # book id of user
# Group is used for multiple users to memorize questions together
# One user will make the share, other users join the group with the code and sync the sharer's book
# The sharer will become the owner and he / she will be able to select some users to be editors
# Each time an editor makes an update on the book, it will be synced to others
# Normal users are not allowed to edit the book
# Editors are also allowed to kick normal users
# The users will see each other on a list and know everyone's progress

# Anyone is allowed to quit the group at any time, when he / she quit the group, 
# the book will become a normal editable book,
# but sync & progress share will stop

cur.execute(f"CREATE TABLE ChallengeData (userId INT, questionId INT, nextChallenge INT, lastChallenge INT)")
# Challenge Data is a table that tells when to display the question next time
# nextChallenge and lastChallenge are both timestamps
# When a new question is added, there should be a record of it with nextChallenge = 0, lastChallenge = -1
# When the user says that he/she memorized the question, then nextChallenge will be extended to a longer time based on forgetting curve
# When the user says that he/she forgot the question, then nextChallenge will be set to 1 hour later

# In challenge mode, the questions to display contains all the questions in the questionlist
# The percentage of showing a question is:
# 35%: Questions that are tagged
# 30%: NextChallenge != 0 && NextChallenge <= int(time.time())
# 30%: NextChallenge == 0
# 5%: Questions that are deleted (to make sure the user still remember it)

cur.execute(f"CREATE TABLE ChallengeRecord (userId INT, questionId INT, memorized INT, timestamp INT)")
# This is the record of historical challenges

# cur.execute(f"CREATE TABLE DeletedQuestionList (userId INT, questionId INT, question VARCHAR(1024), answer VARCHAR(1024), status INT, deleteTimestamp INT)")
# This is the list of all permanently deleted questions (which will never be shown on user side)

cur.execute(f"CREATE TABLE StatusUpdate (userId INT, questionId INT, questionUpdateId INT, updateTo INT, timestamp INT)")
# questionUpdateId is the Id for the specific question
# updateTo is the status the question is updated to
# NOTE: When a new question is added, there should be a StatusUpdate record, with questionUpdateId = 0 and updateTo = 0

cur.execute(f"CREATE TABLE IDInfo (type INT, userId INT, nextId INT)")
cur.execute(f"INSERT INTO IDInfo VALUES (1, -1, 1)")
cur.execute(f"INSERT INTO IDInfo VALUES (4, -1, 1)")
# To store next id of userId 1 / questionId 2 / bookId 3 / groupId 4 / groupQuestionId 5

conn.commit()