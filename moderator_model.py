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

