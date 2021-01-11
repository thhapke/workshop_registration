import string
import secrets

from hdbcli import dbapi

# HANA DB
# config


############
### User Methods
############
def get_moderator(username) :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    sql_command = "select USERNAME, PWDHASH  from DIREGISTER.MODERATORS WHERE USERNAME = \'{}\';".format(username)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return [None,None]
    else :
        return row[0], row[1]

def register_moderator(username,pwdhash) :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    sql_command = "INSERT INTO DIREGISTER.MODERATORS (USERNAME, PWDHASH) VALUES (\'{}\',\'{}\');".format(username,pwdhash)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    cursor.close()
    conn.close()

