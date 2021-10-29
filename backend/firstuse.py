# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import sqlite3
import os, sys
import bcrypt
import json
import random
from functions import *


if os.path.exists("./database.db"):
    t = input("Are you sure to init the database? This will clear the old one if it exists! (Y/N)")
    if t.upper() != "Y":
        print("Aborted")
        sys.exit(0)
    else:
        os.remove("./database.db")


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
# After the 14 days, all of the user's data will be wiped, including UserInfo, WordList, ChallengeData etc
# But his/her userId will persist forever, while it represents an empty account named "Deleted Account"

# If user id becomes a negative number, it means this user has been banned

defaultpwd = hashpwd(config.default_user_password)
cur.execute(f"INSERT INTO UserInfo VALUES (0,'default','None','{defaultpwd}',0,'{genCode(6)}')")
cur.execute(f"INSERT INTO UserEvent VALUES (0, 'register', 0)")
# Default user system's password is 123456
# Clear default account's password after setup (so it cannot be logged in)
# NOTE DO NOT DELETE THE DEFAULT ACCOUNT, keep it in the database record

cur.execute(f"CREATE TABLE Previlege (userId INT, item VARCHAR(32), value INT)")
# User previlege, such as word_limit, word_book_limit, allow_group_creation, group_member_limit

cur.execute(f"CREATE TABLE AdminList (userId INT)")
# Currently this admin list can only be edited from backend using database operations

cur.execute(f"CREATE TABLE WordList (userId INT, wordId INT, word VARCHAR(1024), translation VARCHAR(1024), status INT)")
# wordId is unique for each word, when the word is removed, its wordId will refer to null
# EXAMPLE: WordBook 1 has wordId 1,2 and WordBook 2 has wordId 3
# word and translation are encoded with base64 to prevent datalose
# status is a status code while 1 refers to Default, 2 refers to Tagged and 3 refers to removed
cur.execute(f"CREATE TABLE WordMemorized (userId INT, wordId INT)")

cur.execute(f"CREATE TABLE WordBook (userId INT, wordBookId INT, name VARCHAR(1024))")
cur.execute(f"CREATE TABLE WordBookData (userId INT, wordBookId INT, wordId INT)")
# When a new word is added, it belongs to no word book
# A word can belong to many word books
cur.execute(f"CREATE TABLE WordBookShare (userId INT, wordBookId INT, shareCode VARCHAR(8))")
cur.execute(f"CREATE TABLE WordBookProgress (userId INT, wordBookId INT, progress INT)")

cur.execute(f"CREATE TABLE GroupInfo (groupId INT, owner INT, name VARCHAR(256), description VARCHAR(1024), memberLimit INT, groupCode VARCHAR(8))")
cur.execute(f"CREATE TABLE GroupMember (groupId INT, userId INT, isEditor INT)")
cur.execute(f"CREATE TABLE GroupWord (groupId INT, groupWordId INT, word VARCHAR(1024), translation VARCHAR(1024))")
cur.execute(f"CREATE TABLE GroupSync (groupId INT, userId INT, wordIdOfUser INT, wordIdOfGroup INT)") # word book id of user
cur.execute(f"CREATE TABLE GroupBind (groupId INT, userId INT, wordBookId INT)") # word book id of user
# Group is used for multiple users to memorize words together
# One user will make the share, other users join the group with the code and sync the sharer's word book
# The sharer will become the owner and he / she will be able to select some users to be editors
# Each time an editor makes an update on the word book, it will be synced to others
# Normal users are not allowed to edit the word book
# Editors are also allowed to kick normal users
# The users will see each other on a list and know everyone's progress

# Anyone is allowed to quit the group at any time, when he / she quit the group, 
# the word book will become a normal editable word book,
# but sync & progress share will stop

cur.execute(f"CREATE TABLE ChallengeData (userId INT, wordId INT, nextChallenge INT, lastChallenge INT)")
# Challenge Data is a table that tells when to display the word next time
# nextChallenge and lastChallenge are both timestamps
# When a new word is added, there should be a record of it with nextChallenge = 0, lastChallenge = -1
# When the user says that he/she memorized the word, then nextChallenge will be extended to a longer time based on forgetting curve
# When the user says that he/she forgot the word, then nextChallenge will be set to 1 hour later

# In challenge mode, the words to display contains all the words in the wordlist
# The percentage of showing a word is:
# 35%: Words that are tagged
# 30%: NextChallenge != 0 && NextChallenge <= int(time.time())
# 30%: NextChallenge == 0
# 5%: Words that are deleted (to make sure the user still remember it)

cur.execute(f"CREATE TABLE ChallengeRecord (userId INT, wordId INT, memorized INT, timestamp INT)")
# This is the record of historical challenges

# cur.execute(f"CREATE TABLE DeletedWordList (userId INT, wordId INT, word VARCHAR(1024), translation VARCHAR(1024), status INT, deleteTimestamp INT)")
# This is the list of all permanently deleted words (which will never be shown on user side)

cur.execute(f"CREATE TABLE StatusUpdate (userId INT, wordId INT, wordUpdateId INT, updateTo INT, timestamp INT)")
# wordUpdateId is the Id for the specific word
# updateTo is the status the word is updated to
# NOTE: When a new word is added, there should be a StatusUpdate record, with wordUpdateId = 0 and updateTo = 0

cur.execute(f"CREATE TABLE IDInfo (type INT, userId INT, nextId INT)")
cur.execute(f"INSERT INTO IDInfo VALUES (1, -1, 1)")
cur.execute(f"INSERT INTO IDInfo VALUES (4, -1, 1)")
# To store next id of userId 1 / wordId 2 / wordBookId 3 / groupId 4 / groupWordId 5

conn.commit()