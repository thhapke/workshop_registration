import string
import secrets

from hdbcli import dbapi


# HANA DB
db_host = '559888d5-f0af-4907-ad20-fa4d3876e870.hana.prod-eu10.hanacloud.ondemand.com'
db_user = 'DIREGISTER'
db_pwd = 'Ted2345!'
db_port = '443'


############
### User Methods
############
def get_userlist(event) :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    sql_command = "select USER, PWD,  USERNAME, REGISTRATION_DATE, BUFFER_USER  from DIREGISTER.USERS WHERE EVENT = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    userlist = [{'User': r[0], 'Password': r[1], 'Name': r[2], 'Regist.Time': r[3], 'Buffer User':r[4]} for r in rows]
    return userlist

# remove users from event user list
def reset_userlist(event) :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    sql = "UPDATE DIREGISTER.USERS SET USERNAME = NULL, REGISTRATION_DATE = NULL WHERE EVENT = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql)
    sql = "select USER, PWD, USERNAME, REGISTRATION_DATE, BUFFER_USER  from DIREGISTER.USERS WHERE EVENT = \'{}\';".format(event)
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


def save_users(user_list):
    csv = '\n'.join([','.join(iuser[1:-1]) for iuser in user_list])
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    cursor = conn.cursor()
    # Get all workshops for user deletion
    wss = [w[3]for w in user_list]
    wss = set(wss)
    # DELETE ALL USER
    for w in wss :
        sql = "DELETE FROM DIREGISTER.USERS WHERE EVENT = \'{}\';".format(w)
        cursor.execute(sql)
    sql = 'INSERT INTO DIREGISTER.USERS (EVENT, USER, PWD, BUFFER_USER) VALUES (?, ?,?,?)'
    data = [(user[3],user[1],user[2],user[4]) for user in user_list]
    cursor.executemany(sql, data)
    cursor.close()
    conn.close()

