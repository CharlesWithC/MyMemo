# Copyright (C) 2021 Charles All rights reserved.
# Author: @Charles-1414
# License: GNU General Public License v3.0

import MySQLdb # Install MySQLdb using `apt install python3-mysqldb`
import sqlite3
import os, sys, json
import getpass

from app import app
from functions import hashpwd, genCode, encode

config_txt = open("./config.json","r").read()
config = json.loads(config_txt)

conn = None
cur = None
doinit = False

if config["database"] == "sqlite":
    if not os.path.exists("./database.db"):
        doinit = True
        
    conn = sqlite3.connect("database.db", check_same_thread = False)
    cur = conn.cursor()
    
    app.config['DB_ENABLED'] = True

elif config["database"] == "mysql":
    host = "localhost"
    if not "mysql_host" in config.keys():
        host = input("MySQL Host (e.g. localhost): ")
    else:
        host = config["mysql_host"]

    user = "mymemo"
    if not "mysql_user" in config.keys():
        user = input("MySQL User (e.g. user): ")
    else:
        user = config["mysql_user"]

    passwd = "123456"
    if not "mysql_passwd" in config.keys():
        passwd = getpass.getpass("MySQL Password: ")
    else:
        passwd = config["mysql_passwd"]

    dbname = "mymemo"
    if not "mysql_db" in config.keys():
        dbname = input("MySQL Database (e.g. mymemo): ")
    else:
        dbname = config["mysql_db"]
    
    conn = MySQLdb.connect(host = host, user = user, passwd = passwd, db = dbname)
    cur = conn.cursor()
    cur.execute(f"SHOW TABLES")
    if len(cur.fetchall()) != 34:
        doinit = True
    
    app.config['MYSQL_HOST'] = host
    app.config['MYSQL_USER'] = user
    app.config['MYSQL_PASSWORD'] = passwd
    app.config['MYSQL_DB'] = dbname
    app.config['DB_ENABLED'] = True

else:
    print("Unknown database type, choose one between sqlite and mysql!")
    sys.exit(0)

if doinit:
    print("Initializing database")
    
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

    cur = conn.cursor()
    cur.execute(f"CREATE TABLE UserInfo (userId INT, username VARCHAR(512), bio VARCHAR(1024), email VARCHAR(128), password VARCHAR(256), inviter INT, inviteCode CHAR(8))")
    # encode username
    # Allow only inviting registration mode to prevent abuse
    cur.execute(f"CREATE TABLE UserNameTag (userId INT, tag VARCHAR(32), tagtype VARCHAR(32))")
    # tag: encoded text, like 'Owner'
    # tagtype: tag color
    cur.execute(f"CREATE TABLE UserSettings (userId INT, sRandom INT, sSwap INT, sShowStatus INT, sMode INT, sAutoPlay INT, sTheme VARCHAR(16))")
    cur.execute(f"CREATE TABLE UserEvent (userId INT, event VARCHAR(32), timestamp INT, msg VARCHAR(2048))")
    # Available event: register, login, change_password, delete_account, create_book, delete_book, create_group, 
    # delete_group, join_group, quit_group

    cur.execute(f"CREATE TABLE UserGoal (userId INT, count INT)")
    cur.execute(f"CREATE TABLE CheckIn (userId INT, timestamp INT)")
    # Everyday Goal of passing how many challenges
    # CheckIn can be done after goal is accomplished

    # User should be allowed to delete their accounts
    # When a user request to delete his account, his account will be marked as "Pending for deletion",
    # and will be deleted in 14 days. 
    # During the 14 days, user will be allowed to recover the account. (Like Discord)
    # After the 14 days, all of the user's data will be wiped, including UserInfo, QuestionList, ChallengeData etc
    # But his/her userId will persist forever, while it represents an empty account named "Deleted Account"

    # If user id becomes a negative number, it means this user has been banned

    defaultpwd = hashpwd(config.default_user_password)

    inviteCode = genCode(8)
    print(f"Created default user with invitation code: {inviteCode}")
    cur.execute(f"INSERT INTO UserInfo VALUES (0,'{encode('default')}','','None','{encode(defaultpwd)}',0,'{inviteCode}')")
    cur.execute(f"INSERT INTO UserEvent VALUES (0, 'register', 0, '{encode('Birth of account')}')")
    # Default user system's password is 123456
    # Clear default account's password after setup (so it cannot be logged in)
    # NOTE DO NOT DELETE THE DEFAULT ACCOUNT, keep it in the database record

    cur.execute(f"CREATE TABLE Privilege (userId INT, item VARCHAR(32), value INT)")
    # User privilege, such as question_limit, book_limit, allow_group_creation, group_member_limit

    cur.execute(f"CREATE TABLE AdminList (userId INT)")
    # Currently this admin list can only be edited from backend using database operations

    cur.execute(f"CREATE TABLE QuestionList (userId INT, questionId INT, question VARCHAR(1024), answer VARCHAR(1024), status INT)")
    # questionId is unique for each question, when the question is removed, its questionId will refer to null
    # EXAMPLE: Book 1 has questionId 1,2 and Book 2 has questionId 3
    # question and answer are encoded with base64 to prevent datalose
    # status is a status code while 1 refers to Default, 2 refers to Tagged and 3 refers to removed
    cur.execute(f"CREATE TABLE MyMemorized (userId INT, questionId INT, timestamp INT)")

    cur.execute(f"CREATE TABLE Book (userId INT, bookId INT, name VARCHAR(1024))")
    cur.execute(f"CREATE TABLE BookData (userId INT, bookId INT, questionId INT)")
    # When a new question is added, it belongs to no book
    # A question can belong to many books
    cur.execute(f"CREATE TABLE BookShare (userId INT, bookId INT, shareCode VARCHAR(8))")
    cur.execute(f"CREATE TABLE ShareImport (userId INT, bookId INT, count INT)")
    cur.execute(f"CREATE TABLE BookProgress (userId INT, bookId INT, progress INT)")

    cur.execute(f"CREATE TABLE GroupInfo (groupId INT, owner INT, name VARCHAR(256), description VARCHAR(1024), memberLimit INT, groupCode VARCHAR(8), anonymous INT)")
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

    cur.execute(f"CREATE TABLE StatusUpdate (userId INT, questionId INT, questionUpdateId INT, updateTo INT, timestamp INT)")
    # questionUpdateId is the Id for the specific question
    # updateTo is the status the question is updated to
    # NOTE: When a new question is added, there should be a StatusUpdate record, with questionUpdateId = 0 and updateTo = 0

    cur.execute(f"CREATE TABLE Discovery (discoveryId INT, publisherId INT, bookId INT, title VARCHAR(1024), description VARCHAR(1024), type INT)")
    # title is discovery title
    # description is discovery description
    # type: 1: share | 2: group
    cur.execute(f"CREATE TABLE DiscoveryClick (discoveryId INT, count INT)")
    cur.execute(f"CREATE TABLE DiscoveryLike (discoveryId INT, userId INT, likes INT)")
    cur.execute(f"CREATE TABLE DiscoveryPin (discoveryId INT)")
    # User Id is the user who engaged in this discovery item
    # It could be empty is discovery is public to everyone

    cur.execute(f"CREATE TABLE IDInfo (type INT, userId INT, nextId INT)")
    cur.execute(f"INSERT INTO IDInfo VALUES (1, -1, 1)")
    cur.execute(f"INSERT INTO IDInfo VALUES (4, -1, 1)")
    cur.execute(f"INSERT INTO IDInfo VALUES (6, -1, 1)")
    # To store next id of userId 1 / questionId 2 / bookId 3 / groupId 4 / groupQuestionId 5 / discoveryId 6

    # Sessions
    cur.execute(f"CREATE TABLE ActiveUserLogin (userId INT, token CHAR(46), loginTime INT, expireTime INT, ua VARCHAR(256), ip VARCHAR(128))")
    # Active user login data
    # Remove data when expired / logged out
    # Token = 9-digit-userId + '-' + uuid.uuid(4)

    cur.execute(f"CREATE TABLE UserSessionHistory (userId INT, loginTime INT, logoutTime INT, expire INT, ip VARCHAR(128))")
    # User Session History, updated when user logs out
    # If user logged out manually, then logout time is his/her logout time and "expire" will be set to 0
    # If the token expired, then logout time is the expireTime and "expire" will be set to 1
    # When the user changes his/her password, all of the sessions will be logged out, and expire will be set to 2

    cur.execute(f"CREATE TABLE PendingAccountDeletion (userId INT, deletionTime INT)")

    cur.execute(f"CREATE TABLE PasswordTrial (userId INT, count INT, lastts INT, ip VARCHAR(128))")

    # Temp
    cur.execute(f"CREATE TABLE DataDownloadToken (userId INT, exportType VARCHAR(10), ts INT, token VARCHAR(32))")
    cur.execute(f"CREATE TABLE RequestRecoverAccount (userId INT)")

    conn.commit()