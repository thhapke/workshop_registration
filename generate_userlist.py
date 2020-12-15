from flask import Flask, render_template, Response
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired

import requests
from datetime import datetime
import string
import secrets
import numpy as np

from hdbcli import dbapi

app = Flask(__name__)
app.config['SECRET_KEY'] = 'userListGenthh'

bootstrap = Bootstrap(app)
moment = Moment(app)

# global variable
user_list  = None
event = ''
test_only = True
prefix = 'TAU'

# HANA DB
db_host = 'e3495cba-ef61-4270-9ffd-1094922e42c8.hana.prod-eu10.hanacloud.ondemand.com'
db_user = 'DIREGISTER'
db_pwd = 'Ted2345!'
db_port = '443'

def gen_user(selected_events,prefix,num_user, offset,num_buffer_user,  len_pwd):

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

def get_events() :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    sql_command = "SELECT TITLE, MAX_USER, URL, REGISTRATION_START,REGISTRATION_END,TENANT,EVENT_ID, EVENT_START FROM DIREGISTER.EVENTS;"
    cursor = conn.cursor()
    cursor.execute(sql_command)
    rows = cursor.fetchall()
    events = [{'ID':r[6],'Title':r[0],'Max.User':r[1],'URL':r[2],'Regist.Start':r[3],'Regist.Stop':r[4],'Event Start':r[7]} for r in rows]
    cursor.close()
    conn.close()
    events = sorted(events, key=lambda tup: tup['ID'])
    return events

class EventSelectionForm(FlaskForm):
    #test_only = BooleanField('Test only (no db update)',default=False)
    #event = SelectField('Workshop: ', validators=[DataRequired()])
    selected_events = SelectMultipleField('Workshops (Multi-Selection): ',choices=[], validators=[DataRequired()])
    prefix = StringField('Prefix: ', validators=[DataRequired()],default='TA')
    num_user = IntegerField('Number of User: ', validators=[DataRequired()],default=8)
    offset = IntegerField('Offset: ', default=1)
    num_buffer_user = IntegerField('Number of Buffer User: ', validators=[DataRequired()], default=2)
    len_pwd = IntegerField('Length of Password: ', validators=[DataRequired()],default=8)
    submitpress = SubmitField('Create')

@app.route('/generate', methods = ['GET', 'POST'])
def index():
    global user_list
    global event
    global test_only
    global prefix
    events = get_events()
    event_titles = [(e['ID'], '{} - {} - {}'.format(e['ID'],e['Title'],e['Event Start'])) for e in events]
    form = EventSelectionForm()
    form.selected_events.choices = event_titles

    if form.validate_on_submit() :
        selected_events = form.selected_events.data
        prefix = form.prefix.data
        num_user = form.num_user.data
        offset = form.offset.data
        num_buffer_user = form.num_buffer_user.data
        len_pwd = form.len_pwd.data
        user_list = gen_user(selected_events,prefix,num_user, offset,num_buffer_user,len_pwd)
        user_dictlist = [{'Index':u[0],'Workshop':u[3],'User':u[1],'Password':u[2],'Buffer':u[4]} for u in user_list]

        return  render_template('userlist.html', dictlist = user_dictlist)

    return render_template('generate_user.html',form = form)

@app.route('/downloadsave/')
def downloadsave():
    global user_list
    csv = '\n'.join([','.join(iuser[1:-1]) for iuser in user_list])
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    cursor = conn.cursor()
    # DELETE ALL USER
    sql = "DELETE FROM DIREGISTER.USERS WHERE EVENT = \'{}\';".format(event)
    cursor.execute(sql)
    sql = 'INSERT INTO DIREGISTER.USERS (EVENT, USER, PWD, BUFFER_USER) VALUES (?, ?,?,?)'
    data = [(event,user[1],user[2],user[3]) for user in user_list]
    cursor.executemany(sql, data)
    cursor.close()
    conn.close()

    filename = 'userlist_'+event+'_'+str(len(user_list))+'.csv'
    return Response(csv, mimetype="text/csv", headers={"Content-disposition": "attachment; filename={}".format(filename)})

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
