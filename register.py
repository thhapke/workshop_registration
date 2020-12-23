from flask import Flask, render_template, Blueprint
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

from hdbcli import dbapi

from datetime import datetime

from workshops_model import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DI302020WSTed'

bootstrap = Bootstrap(app)
moment = Moment(app)

# HANA DB
db_host = '559888d5-f0af-4907-ad20-fa4d3876e870.hana.prod-eu10.hanacloud.ondemand.com'
db_user = 'DIREGISTER'
db_pwd = 'Ted2345!'
db_port = '443'

event = ''

register = Blueprint('register', __name__)

class WorkshopsForm(FlaskForm):
    workshop = SelectField('Workshop ', choices=[], validators=[DataRequired()])
    name = StringField('Your name: ', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('notopen.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@register.route('/register', methods = [ 'GET', 'POST'])
def registering():
    global event
    workshops, ws_titles = get_workshops()
    form = WorkshopsForm(ws_titles)
    form.workshop.choices = ws_titles

    if form.validate_on_submit() :
        name = form.name.data
        selected_w = form.workshop.data
        # test if open
        nowt = datetime.utcnow()
        reg_start = workshops[selected_w]['Regist. Start']
        reg_end = workshops[selected_w]['Regist. End']
        if reg_start  and nowt < reg_start:
            msg = "Registration has not been started yet.\nStarting at {} (UTC)".format(reg_start.strftime("%Y-%m-%d, %H:%M"))
            return render_template('notopen.html',msg=msg,event=selected_w)
        if reg_end  and nowt > reg_end:
            msg = "Registration is closed already.\nEnded at {} (UTC)".format(reg_end.strftime("%Y-%m-%d, %H:%M"))
            return render_template('notopen.html', msg=msg, event=selected_w)

        tenant = workshops[selected_w]['Tenant']
        url = workshops[selected_w]['url']
        ws_title = workshops[selected_w]['Title']
        # test if user exist
        user_data = get_user(name,selected_w)
        if user_data :
            return render_template('credentials_exist.html',name = name,user= user_data[1], pwd = user_data[2],
                                   tenant = tenant,url = url,ws_title = ws_title)
        else:
            userpwd = create_user(name,event)
            if not userpwd:
                return render_template('nouser.html', ws_title=event)
            else:
                return render_template('credentials.html',name = name,user= userpwd[0], pwd = userpwd[1],
                                       tenant = tenant,url = url,ws_title = ws_title)

    return render_template('diregisterHANA.html',form = form)


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
