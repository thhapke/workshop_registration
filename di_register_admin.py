from flask import Flask, render_template, Response
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, BooleanField, SelectMultipleField, DateTimeField
from wtforms.validators import DataRequired

import requests
from datetime import datetime, timedelta
import string
import secrets

from hdbcli import dbapi

app = Flask(__name__)
app.config['SECRET_KEY'] = 'userListGenthh'

bootstrap = Bootstrap(app)
moment = Moment(app)

# global variable
event = ''
prefix = 'TAU'
dft_event_id = 'NEW_ID'
dft_title = 'SAP DI Hands-on Workshop'
dft_max_user = 40
dft_tenant = 'default'
dft_url = 'https://vsystem.ingress.dh-ia37o5zq.dhaas-live.shoot.live.k8s-hana.ondemand.com/login/?redirectUrl=%2Flogin%2F%3FredirectUrl%3D%252Fapp%252Fdatahub-app-launchpad%252F&tenant=default'
dt_format = '%Y-%m-%d %H:%M'
dft_pwd = 'Welcome01'


# HANA DB
db_host = 'e3495cba-ef61-4270-9ffd-1094922e42c8.hana.prod-eu10.hanacloud.ondemand.com'
db_user = 'DIREGISTER'
db_pwd = 'Ted2345!'
db_port = '443'


############
### Forms
############
class UserGenerationSelectForm(FlaskForm):
    selected_events = SelectMultipleField('Workshops (Multi-Selection): ',choices=[], validators=[DataRequired()])
    prefix = StringField('Prefix: ', validators=[DataRequired()],default='TA')
    num_user = IntegerField('Number of User: ', validators=[DataRequired()],default=8)
    offset = IntegerField('Offset: ', default=1)
    num_buffer_user = IntegerField('Number of Buffer User: ', validators=[DataRequired()], default=2)
    static_pwd = BooleanField('Static Password: ', validators=[DataRequired()],default=True)
    len_pwd = IntegerField('Length of Password: ', validators=[DataRequired()],default=8)
    default_pwd = StringField('Default Password: ',validators=[DataRequired()], default=dft_pwd)
    submit = SubmitField('Create')

class MonitorSelectForm(FlaskForm):
    selected_event = SelectField('',choices=[], validators=[DataRequired()])
    selected_event.label = None
    submit = SubmitField('Submit')

class EditForm(FlaskForm):
    selected_event = SelectField('Workshops',choices=[], validators=[DataRequired()])
    submitget = SubmitField('Get')
    event_id = StringField('Event ID: ', validators=[DataRequired()],default=dft_event_id)
    title = StringField('Title: ', validators=[DataRequired()],default=dft_title)
    now_dt = datetime.utcnow()
    event_dt = now_dt + timedelta(hours=1) - timedelta(minutes=now_dt.minute)
    event_startdate = DateTimeField('Event Start Datetime (Example: 2020-12-31 9:30)',validators=[DataRequired()],format=dt_format,default=event_dt)
    regstart_dt = event_dt - timedelta(hours=1)
    reg_startdate = DateTimeField('Registration Start Datetime (Example: 2020-12-31 9:30)',validators=[DataRequired()],format=dt_format,default=regstart_dt)
    regstop_dt = event_dt + timedelta(minutes=15)
    reg_enddate = DateTimeField('Registration End Datetime (Example: 2020-12-31 9:30)', validators=[DataRequired()], format=dt_format,default=regstop_dt)
    max_user = IntegerField("Maximum User",validators=[DataRequired()],default=dft_max_user)
    tenant = StringField('Tenant: ', validators=[DataRequired()],default=dft_tenant)
    url = StringField('System ULR: ', validators=[DataRequired()],default= dft_url)
    submitsave = SubmitField('Save')
    submitremove = SubmitField('Remove')

class EventFilter(FlaskForm) :
    incl_ended = BooleanField('Include \"ended registration\"-workshops',default=False)
    submitrefresh = SubmitField('Refresh')

############
### Event Methods
############
def get_events(incl_ended = False) :
    nowtime = datetime.utcnow().strftime("%Y-%m-%d, %H:%M")
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    if incl_ended :
        sql_command = "SELECT EVENT_ID,TITLE,EVENT_START,REGISTRATION_START,REGISTRATION_END,MAX_USER, TENANT, URL "\
                      "FROM DIREGISTER.EVENTS;"
    else :
        sql_command = "SELECT EVENT_ID,TITLE,EVENT_START,REGISTRATION_START,REGISTRATION_END,MAX_USER, TENANT, URL "\
                      "FROM DIREGISTER.EVENTS WHERE REGISTRATION_END > \'{}\';".format(nowtime)

    cursor = conn.cursor()
    cursor.execute(sql_command)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # return result as
    #  * list of dictionaries or
    #  * list of 1 dictionary with empty values
    if len(rows) > 0 :
        srows = sorted(rows, key=lambda k: k[0])
        events = [{'ID':r[0],'Title':r[1],'Event Start':r[2],'Regist. Start':r[3],'Regist. End':r[4],'Max. User':r[5],\
                   'Tenant':r[6],'url':r[7]} for r in srows]
        event_titles = [(e['ID'], '{} - {} - {}'.format(e['ID'], e['Title'], e['Event Start'])) for e in events]
    else :
        events = [{'ID':"",'Title':"",'Event Start':"",'Regist. Start':"",'Regist. End':"",'Max. User':"",\
                   'Tenant':"",'url':""}]
        event_titles = []
    return events, event_titles

def get_event(event_id) :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )

    sql_command = "SELECT EVENT_ID,TITLE,EVENT_START,REGISTRATION_START,REGISTRATION_END,MAX_USER, TENANT, URL "\
                  "FROM DIREGISTER.EVENTS WHERE EVENT_ID = \'{}\';".format(event_id)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    event = {'ID':row[0],'Title':row[1],'Event Start':row[2],'Regist. Start':row[3],'Regist. End':row[4],'Max. User':row[5],\
               'Tenant':row[6],'url':row[7]}
    return event

def save_event(record) :
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "UPSERT DIREGISTER.EVENTS  VALUES" \
                  "(\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\') WITH PRIMARY KEY;".format(*record)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    cursor.close()
    conn.close()
    return

def remove_event(event_id) :
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "DELETE FROM DIREGISTER.EVENTS WHERE EVENT_ID = \'{}\';".format(event_id)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    cursor.close()
    conn.close()

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
def generate_userlist(selected_events, prefix, num_user, offset, num_buffer_user, len_pwd,dft_password,static_pwd):

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
            password = dft_password
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

############
### BINDINGS
############
@app.route('/', methods = ['GET', 'POST'])
def index():
    events, select_titles = get_events(incl_ended=False)
    eventform = EventFilter()

    if eventform.validate_on_submit():
        incl_ended = eventform.incl_ended.data
        events, select_titles = get_events(incl_ended)

    return render_template('events.html',form = eventform,dictlist=events)

@app.route('/monitor', methods = ['GET', 'POST'])
def monitor():
    events, select_titles = get_events(incl_ended = True)
    form = MonitorSelectForm()
    form.selected_event.choices = select_titles
    if form.validate_on_submit() :
        event = form.selected_event.data
        user_list = get_userlist(event)
        return  render_template('userlist_monitor.html',dictlist = user_list,event = event )

    return render_template('event_selection_monitor.html',form = form,dictlist = events)

@app.route('/generate', methods = ['GET', 'POST'])
def generate():
    global event
    global prefix
    events, select_titles = get_events(incl_ended = True)
    form = UserGenerationSelectForm()
    form.selected_events.choices = select_titles
    if form.validate_on_submit() :
        user_list = generate_userlist(selected_events=form.selected_events.data,
                                      prefix = form.prefix.data,
                                      num_user=form.num_user.data,
                                      offset=form.offset.data,
                                      num_buffer_user=form.num_buffer_user.data,
                                      len_pwd=form.len_pwd.data,
                                      dft_password= form.default_pwd.data,
                                      static_pwd=form.static_pwd.data)
        user_dictlist = [{'Index':u[0],'Workshop':u[3],'User':u[1],'Password':u[2],'Buffer':u[4]} for u in user_list]

        return  render_template('userlist.html', dictlist = user_dictlist)

    return render_template('generate_user.html',form = form)

@app.route('/edit', methods = ['GET', 'POST'])
def edit():
    form = EditForm()
    events, select_titles = get_events(incl_ended = True)
    select_titles.insert(0,('NEW','NEW'))
    form.selected_event.choices = select_titles
    if form.validate_on_submit() and form.submitget.data  :
        event_selected = form.selected_event.data
        # POPULATE Selected EVENT
        if event_selected == 'NEW' :
            form.event_id.data = dft_event_id
            form.title.data = dft_title
            now_dt = datetime.utcnow()
            event_dt = now_dt + timedelta(hours=1) - timedelta(minutes=now_dt.minute)
            form.event_startdate.data = event_dt.strftime(dt_format)
            form.reg_startdate.data = (event_dt - timedelta(hours=1)).strftime(dt_format)
            form.reg_enddate.data = (event_dt + timedelta(minutes=15)).strftime(dt_format)
            form.max_user.data = dft_max_user
            form.tenant.data = dft_tenant
            form.url.data = dft_url
        else :
            # POPULATE NEW EVENT
            event = get_event(event_selected)
            form.event_id.data = event['ID']
            form.title.data = event['Title']
            form.event_startdate.data = event["Event Start"]
            form.reg_startdate.data = event["Regist. Start"]
            form.reg_enddate.data = event["Regist. End"]
            form.max_user.data = event['Max. User']
            form.tenant.data = event['Tenant']
            form.url.data = event['url']
    # SAVE EVENT
    elif form.validate_on_submit() and form.submitsave.data:
        record = [form.title.data,form.max_user.data,form.url.data,form.reg_startdate.data,form.reg_enddate.data,
                  form.tenant.data,form.event_id.data,form.event_startdate.data]
        save_event(record)
    # REMOVE EVENT
    elif form.validate_on_submit() and form.submitremove.data:
        remove_event(form.event_id.data)
        form.event_id.data = dft_event_id
        form.title.data = dft_title
        now_dt = datetime.utcnow()
        event_dt = now_dt + timedelta(hours=1) - timedelta(minutes=now_dt.minute)
        form.event_startdate.data = event_dt.strftime(dt_format)
        form.reg_startdate.data = (event_dt - timedelta(hours=1)).strftime(dt_format)
        form.reg_enddate.data = (event_dt + timedelta(minutes=15)).strftime(dt_format)
        form.max_user.data = dft_max_user
        form.tenant.data = dft_tenant
        form.url.data = dft_url
        events, select_titles = get_events(incl_ended = True)
        select_titles.insert(0, ('NEW', 'NEW'))
        form.selected_event.choices = select_titles
    return render_template('edit.html', form = form)

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
