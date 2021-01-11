
from datetime import datetime, timedelta

from hdbcli import dbapi


# HANA DB
#config.cfg


def get_workshops(user_id) :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )

    sql = "SELECT ID,TITLE,WORKSHOP_START,REGISTRATION_START,REGISTRATION_END,MAX_USER, INFO, URL, MODERATOR "\
                 "FROM DIREGISTER.WORKSHOPS"

    if not (user_id == 'wradmin' or user_id == 'anonymous') :
        sql = sql + " WHERE MODERATOR=\'{}\'".format(user_id)
    sql = sql + ';'

    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # return result as
    #  * list of dictionaries or
    #  * list of 1 dictionary with empty values
    if len(rows) > 0 :
        srows = sorted(rows, key=lambda k: k[0])
        wss = {r[0]:{'ID':r[0],'Title':r[1],'Moderator':r[8],'Workshop Start':r[2],'Regist. Start':r[3],'Regist. End':r[4],'Max. User':r[5],\
                   'Info':r[6],'url':r[7]} for r in srows}
        ws_titles = [(e['ID'], '{} - {} - {}'.format(e['ID'], e['Title'], e['Workshop Start'])) for k,e in wss.items()]
    else :
        wss = {' ':{'ID':"",'Title':"",'Moderator':"",'Workshop Start':"",'Regist. Start':"",'Regist. End':"",'Max. User':"",\
                   'Info':"",'url':""}}
        ws_titles = []
    return wss, ws_titles

def get_workshop(user_id,workhop_id ) :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )

    sql_command = "SELECT ID,TITLE,WORKSHOP_START,REGISTRATION_START,REGISTRATION_END,MAX_USER, INFO, URL, MODERATOR "\
                  "FROM DIREGISTER.WORKSHOPS WHERE ID = \'{}\';".format(workhop_id)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row == None :
        return 'Workshop does not exist.', None

    ws = {'ID':row[0],'Title':row[1],'Moderator':row[8],'Workshop Start':row[2],'Regist. Start':row[3],'Regist. End':row[4],\
          'Max. User':row[5],'Info':row[6],'url':row[7]}

    if not ws['Moderator'] == user_id :
        return 'User ID does not match Moderator', None

    return '0',ws

def save_event(record,user_id) :
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "UPSERT DIREGISTER.WORKSHOPS (\"ID\",\"TITLE\",\"MAX_USER\",\"URL\",\"WORKSHOP_START\",\"REGISTRATION_START\","\
                  "\"REGISTRATION_END\",\"INFO\",\"MODERATOR\") VALUES" \
                  "(\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\') WITH PRIMARY KEY;"\
                .format(record['id'],record['title'],record['max_user'],record['url'],record['workshop_start'],record['registration_start'],\
                        record['registration_end'],record['info'],user_id)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    cursor.close()
    conn.close()
    return

def remove_event(ws_id) :
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "DELETE FROM DIREGISTER.WORKSHOPS WHERE ID = \'{}\';".format(ws_id)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    cursor.close()
    conn.close()
