import string
import secrets

import datetime
import pytz

from hdbcli import dbapi


############
### User Methods
############
def get_userlist(event,db) :
    conn = dbapi.connect(address=db['host'],port=db['port'],user=db['user'],password=db['pwd'],encrypt=True, sslValidateCertificate=False )
    sql_command = "select USER, PWD,  USERNAME, REGISTRATION_DATE, BUFFER_USER  from DIREGISTER.USERS WHERE WORKSHOP_ID = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    userlist = [{'User': r[0], 'Password': r[1], 'Name': r[2], 'Regist.Time': r[3], 'Buffer User':r[4]} for r in rows]
    return userlist

# remove users from event user list
def reset_userlist(event,db) :
    conn = dbapi.connect(address=db['host'],port=db['port'],user=db['user'],password=db['pwd'],encrypt=True, sslValidateCertificate=False )
    sql = "UPDATE DIREGISTER.USERS SET USERNAME = NULL, REGISTRATION_DATE = NULL WHERE WORKSHOP_ID = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql)
    sql = "select USER, PWD, USERNAME, REGISTRATION_DATE, BUFFER_USER  from DIREGISTER.USERS WHERE WORKSHOP_ID = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    userlist = [{'User': r[0], 'Password': r[1], 'Name': r[2], 'Regist.Time': r[3], 'Buffer User':r[4]}for r in rows]
    return userlist

# Generate User Passwords
def generate_userlist(selected_events, prefix, num_user, offset, num_buffer_user, len_pwd,default_pwd,static_pwd):

    # User and pwd
    zfillnum = 3 if (num_user + offset) * len(selected_events) > 100 else 2
    all_event_user = num_user + num_buffer_user

    # set of chars from which to choose password chars
    baseset = string.ascii_letters + string.digits
    baseset = [i for i in baseset if not i in 'Il0O']

    # create passwords from baseset that containts at least one upper-, lowercase and digit
    iup = list()
    index = 0
    for evi, ev in enumerate(selected_events) :
        for i in range(0, all_event_user) :
            # find passwords
            password = default_pwd
            if not static_pwd :
                while True:
                    password = ''.join(secrets.choice(baseset) for i in range(len_pwd))
                    if (any(c.islower() for c in password)
                            and any(c.isupper() for c in password)
                            and sum(c.isdigit() for c in password)>0 ):
                        break
            buffer = 'Y' if i >= num_user else ''
            iup.append([str(index),prefix + str(index+offset).zfill(zfillnum),password,selected_events[evi],buffer])
            index += 1

    return iup


def save_users(user_list,db):
    conn = dbapi.connect(address=db['host'],port=db['port'],user=db['user'],password=db['pwd'], encrypt=True,
                         sslValidateCertificate=False)
    cursor = conn.cursor()
    # Get all workshops for user deletion
    wss = [w['Workshop']for w in user_list]
    wss = set(wss)
    # DELETE ALL USER
    for w in wss :
        sql = "DELETE FROM DIREGISTER.USERS WHERE WORKSHOP_ID = \'{}\';".format(w)
        cursor.execute(sql)
    sql = 'INSERT INTO DIREGISTER.USERS (WORKSHOP_ID, USER, PWD, BUFFER_USER) VALUES (?, ?,?,?)'
    data = [(user['Workshop'],user['User'],user['Password'],user['Buffer']) for user in user_list]
    cursor.executemany(sql, data)
    cursor.close()
    conn.close()

def get_user(username,event,db) :
    conn = dbapi.connect(address=db['host'],port=db['port'],user=db['user'],password=db['pwd'], encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "SELECT * FROM DIREGISTER.USERS WHERE \"WORKSHOP_ID\" = \'{}\' AND \"USERNAME\" = \'{}\';".format(event,username)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    row = cursor.fetchone()
    if row :
        return row
    else :
        return None
    cursor.close()
    conn.close()

def create_user(user_name,event,db) :
    conn = dbapi.connect(address=db['host'],port=db['port'],user=db['user'],password=db['pwd'], encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "SELECT TOP 1 USER,PWD FROM DIREGISTER.USERS WHERE USERNAME IS NULL AND BUFFER_USER != 'Y' AND WORKSHOP_ID = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    record = cursor.fetchone()
    if not record :
        return None
    nowt = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d, %H:%M:%S")
    sql_command = "UPDATE DIREGISTER.USERS SET USERNAME = \'{}\', REGISTRATION_DATE = \'{}\' WHERE USER = \'{}\' AND WORKSHOP_ID = \'{}\' ;".\
        format(user_name,nowt,record[0],event)
    cursor.execute(sql_command)
    cursor.close()
    conn.close()
    return record
