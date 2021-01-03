from flask import Flask, render_template, Response
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired

import requests
from datetime import datetime
import string
import secrets

from hdbcli import dbapi

app = Flask(__name__)
app.config['SECRET_KEY'] = 'userListGenthh'

bootstrap = Bootstrap(app)
moment = Moment(app)

# global variable
user_list  = None
event = ''

# HANA DB
db_host = 'e3495cba-ef61-4270-9ffd-1094922e42c8.hana.prod-eu10.hanacloud.ondemand.com'
db_user = 'DIREGISTER'
db_pwd = 'Ted2345!'
db_port = '443'

event = ''

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


def get_events() :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    sql_command = "SELECT EVENT_ID,TITLE,EVENT_START,REGISTRATION_START,REGISTRATION_END,MAX_USER, TENANT, URL "\
                  "FROM DIREGISTER.EVENTS;"
    cursor = conn.cursor()
    cursor.execute(sql_command)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    events = [
        {'ID': r[0], 'Title': r[1], 'Event Start': r[2], 'Regist.Start': r[3], 'Regist.End': r[4], 'Max User': r[5], \
         'Tenant': r[6], 'url': r[7], } for r in rows]
    return events

class EventSelectionForm(FlaskForm):
    def __init__(self,ws_list):
        super(EventSelectionForm,self).__init__()
        self.selected_event.choices = ws_list
    selected_event = SelectField('Event ', choices=[], validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/userlist', methods = ['GET', 'POST'])
def refresh() :
    user_list = get_userlist(event)
    return render_template('userlist_monitor.html', dictlist=user_list)

@app.route('/reset', methods = ['GET', 'POST'])
def reset() :
    user_list = reset_userlist(event)
    return render_template('userlist_monitor.html', dictlist=user_list)

@app.route('/', methods = ['GET', 'POST'])
def index():
    global user_list
    global event

    events = get_events()
    event_titles = [ et['ID'] for et in events]
    form = EventSelectionForm(event_titles)
    form.selected_event.choices = event_titles

    if form.validate_on_submit() :
        event = form.selected_event.data
        user_list = get_userlist(event)
        return  render_template('userlist_monitor.html', dictlist = user_list, event = event)

    return render_template('workshop_selection_monitor.html', form = form, dictlist = events)


if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
