from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

from hdbcli import dbapi

from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DI302020WSTed'

bootstrap = Bootstrap(app)
moment = Moment(app)

# HANA DB
db_host = 'e3495cba-ef61-4270-9ffd-1094922e42c8.hana.prod-eu10.hanacloud.ondemand.com'
db_user = 'DIREGISTER'
db_pwd = 'Ted2345!'
db_port = '443'

event = ''

class NameForm(FlaskForm):
    def __init__(self,ws_list):
        super(NameForm,self).__init__()
        self.workshop.choices = ws_list

    workshop = SelectField('Workshop ', choices=[], validators=[DataRequired()])
    name = StringField('Your name: ', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('notopen.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods = [ 'GET', 'POST'])
def index():
    global event
    events = get_workshops()
    ws_titles = [(e['title_id'] , e['title_id'] + ' - ' + e['title']) for e in events]
    form = NameForm(ws_titles)

    if form.validate_on_submit() :
        name = form.name.data
        event = form.workshop.data
        ut = [ (e['url'],e['tenant']) for e in events if e['title_id'] == event]
        # test if open
        msg = registering_open(event)
        if  msg :
            return render_template('notopen.html', msg=msg, event=event)

        # test if user exist
        user_data = get_user(name,event)
        if user_data :
            return render_template('credentials_exist.html',name = name,user= user_data[1], pwd = user_data[2],
                                   tenant = ut[0][1],url = ut[0][0],ws_title = event)
        else:
            userpwd = create_user(name,event)
            if not userpwd:
                return render_template('nouser.html', ws_title=event)
            else:
                return render_template('credentials.html',name = name,user= userpwd[0], pwd = userpwd[1],
                                       tenant = ut[0][1],url = ut[0][0],ws_title = event)

    return render_template('diregisterHANA.html',form = form)


def get_workshops() :
    conn = dbapi.connect(address=db_host,port=db_port,user=db_user,password=db_pwd,encrypt=True, sslValidateCertificate=False )
    sql_command = "select TITLE, MAX_USER, URL, REGISTRATION_START,REGISTRATION_END,TENANT,TITLE_ID  from DIREGISTER.EVENTS;"
    cursor = conn.cursor()
    cursor.execute(sql_command)
    rows = cursor.fetchall()
    events = [{'title':r[0],'max_user':r[1],'url':r[2],'start':r[3],'stop':r[4],'tenant':r[5],'title_id':r[6]} for r in rows]
    cursor.close()
    conn.close()
    return events

def registering_open(event) :
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "SELECT REGISTRATION_START, REGISTRATION_END FROM DIREGISTER.EVENTS WHERE \"TITLE_ID\" = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    nowt = datetime.utcnow()
    if row[0] != '' and row[0] != None and nowt < row[0]:
        return "Registration has not been started yet.\nStarting at {} (UTC)".format(row[0].strftime("%Y-%m-%d, %H:%M"))
    if row[0] != '' and row[0] != None and nowt > row[1]:
        return "Registration is closed already.\nEnded at {} (UTC)".format(row[1].strftime("%Y-%m-%d, %H:%M"))
    return None

def get_user(username,event) :
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "SELECT * FROM DIREGISTER.USERS WHERE \"EVENT\" = \'{}\' AND \"USERNAME\" = \'{}\';".format(event,username)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    row = cursor.fetchone()
    if row :
        return row
    else :
        return None
    cursor.close()
    conn.close()

def create_user(user_name,event) :
    conn = dbapi.connect(address=db_host, port=db_port, user=db_user, password=db_pwd, encrypt=True,
                         sslValidateCertificate=False)
    sql_command = "SELECT TOP 1 USER,PWD FROM DIREGISTER.USERS WHERE USERNAME IS NULL AND BUFFER_USER != 'Y' AND EVENT = \'{}\';".format(event)
    cursor = conn.cursor()
    cursor.execute(sql_command)
    record = cursor.fetchone()
    if not record :
        return None
    nowt = datetime.utcnow().strftime("%Y-%m-%d, %H:%M:%S")
    sql_command = "UPDATE DIREGISTER.USERS SET USERNAME = \'{}\', REGISTRATION_DATE = \'{}\' WHERE USER = \'{}\' AND EVENT = \'{}\' ;".\
        format(user_name,nowt,record[0],event)
    cursor.execute(sql_command)
    cursor.close()
    conn.close()
    return record

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
