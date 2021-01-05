from flask import Flask, render_template, Response, session, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from flask_login import login_user, LoginManager, UserMixin, login_required, logout_user
from wtforms import StringField, SubmitField, IntegerField, SelectField, BooleanField, SelectMultipleField, DateTimeField, PasswordField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from register import register
from workshops_model import *
from users_model import *
from moderator_model import get_moderator, register_moderator
from datetime import datetime

import os
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = 'userListGenthh'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.csv']
app.register_blueprint(register)

bootstrap = Bootstrap(app)
moment = Moment(app)


# global variable
prefix = 'TAU'
dft_event_id = 'NEW_ID'
dft_title = 'workshop'
dft_max_user = 40
dft_info = ''
dft_url = 'https://wwww.workshop.com/system'
dt_format = '%Y-%m-%d %H:%M'
dft_pwd = 'Welcome01'
incl_ended = False


############
#### Login
############
login_manager = LoginManager()
login_manager.init_app(app)
admin_id = 'thhadmin'
admin_pwd = 'thh2Reg4'

class User(UserMixin) :
    def __init__(self,user):
        self.username, self.password_hash = get_moderator(user)
        self.id = self.username

    @property
    def password(self):
        raise AttributeError('Password not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')

############
### Forms
############
class UserGenerationSelectForm(FlaskForm):
    selected_events = SelectMultipleField('Workshops (Multi-Selection): ',choices=[], validators=[DataRequired()])
    prefix = StringField('Prefix: ', validators=[DataRequired()],default='TA')
    num_user = IntegerField('Number of User: ', validators=[DataRequired()],default=8)
    offset = IntegerField('Offset: ', default=1)
    num_buffer_user = IntegerField('Number of Buffer User: ', validators=[DataRequired()], default=2)
    len_pwd = IntegerField('Length of Password: ', validators=[DataRequired()],default=8)
    static_pwd = BooleanField('Static Password: ', default=True)
    default_pwd = StringField('Default Password: ',validators=[DataRequired()], default=dft_pwd)
    submit = SubmitField('Create')

class UserUploadForm(FlaskForm):
    selected_events = SelectMultipleField('Workshops (Multi-Selection): ',choices=[], validators=[DataRequired()])
    usercsv = FileField('Document', validators=[FileRequired(), FileAllowed(['csv'], 'csv only!')])
    num_buffer = IntegerField('Number of Buffer User',default=0)
    uploadsubmit = SubmitField('Upload')

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
    info = StringField('Info: ', validators=[DataRequired()])
    url = StringField('System ULR: ', validators=[DataRequired()],default= dft_url)
    submitsave = SubmitField('Save')
    submitremove = SubmitField('Remove')

class UserListForm(FlaskForm) :
    savesubmit = SubmitField('Save')
    downloadsubmit = SubmitField('Download')

class LoginForm(FlaskForm) :
    username = StringField('User Name',validators=[])
    password = PasswordField('Password',validators=[])
    submitlogin = SubmitField('Log In')
    submitlogout = SubmitField('Log Out')
    submitregister = SubmitField('Register')

############
### BINDINGS
############
@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit() :
        if form.submitlogin.data :
            user = User(form.username.data)
            if not user.username :
                flash('Unregisterd user: {}'.format(form.username.data))
            else :
                if not user.verify_password(form.password.data) :
                    flash('Invalid password.')
                else :
                    login_user(user)
                    return redirect(url_for('index'))
        elif form.submitregister.data  :
            if len(form.password.data) < 6 :
                flash('Minimum length of password: 6.')
            elif len(form.username.data) < 6 :
                flash('Minimum length of user name: 6.')
            else :
                register_moderator(form.username.data,generate_password_hash(form.password.data))
                user = User(form.username.data)
                login_user(user)
                return redirect(url_for('index'))
        else :
            logout_user()
            flash('You have been logged out.')

    return render_template('login.html',form=form)


@app.route('/', methods = ['GET', 'POST'])
@login_required
def index():
    workshops, select_titles = get_workshops(user_id=session['_user_id'])

    tbody = list()
    theader = list()
    if len(workshops) > 0 :
        tbody = list(workshops.values())
        theader = tbody[0].keys()

    return render_template('workshops.html',table_header =theader,table_body=tbody,user_id=session['_user_id'])


@app.route('/monitor', methods = ['GET', 'POST'])
@login_required
def monitor():
    workshops, select_titles = get_workshops(user_id=session['_user_id'])
    form = MonitorSelectForm()
    form.selected_event.choices = select_titles
    if form.validate_on_submit() :
        workshop = form.selected_event.data
        user_list = get_userlist(workshop)
        return  render_template('userlist_monitor.html',dictlist = user_list,event = workshop,user_id=session['_user_id'])

    return render_template('workshop_selection_monitor.html',form = form,dictlist = list(workshops.values()), user_id=session['_user_id'])

@app.route('/generate', methods = ['GET', 'POST'])
@login_required
def generate():
    events, select_titles = get_workshops(user_id=session['_user_id'])
    form = UserGenerationSelectForm()
    form.selected_events.choices = select_titles
    if form.validate_on_submit() :
        user_list = generate_userlist(selected_events=form.selected_events.data,
                                      prefix=form.prefix.data,
                                      num_user=form.num_user.data,
                                      offset=form.offset.data,
                                      num_buffer_user=form.num_buffer_user.data,
                                      len_pwd=form.len_pwd.data,
                                      default_pwd=form.default_pwd.data,
                                      static_pwd=form.static_pwd.data)

        session['userlist'] = [{'Index': u[0], 'Workshop': u[3], 'User': u[1], 'Password': u[2], 'Buffer': u[4]} for u in
                         user_list]

        return redirect(url_for('userlist'))

    return render_template('generate_user.html',form = form, user_id=session['_user_id'])

@app.route('/upload', methods = ['GET', 'POST'])
@login_required
def upload():
    workshops, select_titles = get_workshops(user_id=session['_user_id'])
    form = UserUploadForm()
    form.selected_events.choices = select_titles
    if form.validate_on_submit() :
        session['workshop_ids'] = form.selected_events.data
        num_buffer = form.num_buffer.data
        filename = form.usercsv.data.filename
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            abort(400)
        user_df = pd.read_csv(form.usercsv.data,header=None,names=['User','Password'])
        user_ws_df = pd.DataFrame(columns=['User','Password','Workshop','Buffer'])
        for w in form.selected_events.data :
            user_df['Workshop'] = w
            user_df['Buffer'] = ''
            user_df.tail(num_buffer)['Buffer'] = 'Y'
            user_ws_df = user_ws_df.append(user_df.copy(),ignore_index=True)
        user_ws_df['Index'] = user_ws_df.index
        user_ws_df['Index'] = user_ws_df['Index'].astype('int16')
        session['userlist'] = user_ws_df.to_dict(orient='records')
        return redirect(url_for('userlist'))

    return render_template('upload.html',form = form, user_id=session['_user_id'])


@app.route('/userlist', methods = ['GET', 'POST'])
@login_required
def userlist() :

    user_list = session['userlist']
    # sort dict
    user_list = [{'Index':ul['Index'],'User':ul['User'],'Password':ul['Password'],'Workshop':ul['Workshop'],'Buffer':ul['Buffer']} for ul in user_list]
    form = UserListForm()

    if form.validate_on_submit() :
        if form.savesubmit.data :
            save_users(user_list=user_list)
            flash('User list saved to database!')
        elif form.downloadsubmit.data :
            filename = 'userlist_sf.csv'
            csv = '\n'.join(['{},{},{},{}'.format(u['User'],u['Password'],u['Workshop'],u['Buffer']) for u in user_list])
            flash('User list downloaded!')
            return Response(csv, mimetype="text/csv", headers={"Content-disposition": "attachment; filename={}".format('userlist_resp.csv')})

    return render_template('userlist.html', form = form,dictlist=user_list,user_id = session['_user_id'])


@app.route('/edit', methods = ['GET', 'POST'])
@login_required
def edit():
    form = EditForm()
    workshops, ws_titles = get_workshops(user_id=session['_user_id'])
    ws_titles.insert(0,('NEW','NEW'))
    form.selected_event.choices = ws_titles
    if form.validate_on_submit() and form.submitget.data  :
        ws_selected = form.selected_event.data
        # POPULATE Selected EVENT
        if ws_selected == 'NEW' :
            form.event_id.data = dft_event_id
            form.title.data = dft_title
            now_dt = datetime.utcnow()
            event_dt = now_dt + timedelta(hours=1) - timedelta(minutes=now_dt.minute)
            form.event_startdate.data = event_dt.strftime(dt_format)
            form.reg_startdate.data = (event_dt - timedelta(hours=1)).strftime(dt_format)
            form.reg_enddate.data = (event_dt + timedelta(minutes=15)).strftime(dt_format)
            form.max_user.data = dft_max_user
            form.info.data =''
            form.url.data = dft_url
        else :
            # POPULATE NEW EVENT
            msg, workshop = get_workshop(user_id=session['_user_id'],workhop_id=ws_selected)
            if not msg =='0' :
                flash(msg)
            else :
                form.event_id.data = workshop['ID']
                form.title.data = workshop['Title']
                form.event_startdate.data = workshop["Workshop Start"]
                form.reg_startdate.data = workshop["Regist. Start"]
                form.reg_enddate.data = workshop["Regist. End"]
                form.max_user.data = workshop['Max. User']
                form.info.data = workshop['Info']
                form.url.data = workshop['url']
    # SAVE EVENT
    elif form.validate_on_submit() and form.submitsave.data:
        record = {'title':form.title.data,'max_user':form.max_user.data,'url':form.url.data,'registration_start':form.reg_startdate.data,\
                  'registration_end':form.reg_enddate.data,'info':form.info.data,'id':form.event_id.data,'workshop_start':form.event_startdate.data}
        save_event(record,user_id=session['_user_id'])
        flash('Workshop saved: {}'.format(record['id']))

    # REMOVE EVENT
    elif form.validate_on_submit() and form.submitremove.data:
        removed_workshop = form.event_id.data
        remove_event(form.event_id.data)
        form.event_id.data = dft_event_id
        form.title.data = dft_title
        now_dt = datetime.utcnow()
        event_dt = now_dt + timedelta(hours=1) - timedelta(minutes=now_dt.minute)
        form.event_startdate.data = event_dt.strftime(dt_format)
        form.reg_startdate.data = (event_dt - timedelta(hours=1)).strftime(dt_format)
        form.reg_enddate.data = (event_dt + timedelta(minutes=15)).strftime(dt_format)
        form.max_user.data = dft_max_user
        form.info.data = dft_info
        form.url.data = dft_url
        workshops, ws_titles = get_workshops(incl_ended = True)
        ws_titles.insert(0, ('NEW', 'NEW'))
        form.selected_event.choices = ws_titles
        flash('Workshop removed: {}'.format(removed_workshop))
    return render_template('edit.html', form = form, user_id = session['_user_id'] )


@app.route('/help', methods = ['GET', 'POST'])
def help():
    return render_template("README.html")


if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
