from flask import Flask, render_template, Blueprint, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired

from workshops_model import *
from users_model import *

app = Flask(__name__)
app.config.from_object('config.Config')
db = {'host':app.config['HDB_URI'],'user':app.config['HDB_USER'],'pwd':app.config['HDB_PWD'],'port':app.config['HDB_PORT']}

bootstrap = Bootstrap(app)
moment = Moment(app)

register = Blueprint('register', __name__)

class WorkshopsForm(FlaskForm):
    workshop = SelectField('Workshop ', choices=[], validators=[DataRequired()])
    name = StringField('Your name: ', validators=[DataRequired()])
    submit = SubmitField('Submit')


@register.route('/register/<moderator>', methods = [ 'GET', 'POST'])
def registering(moderator):
    workshops, ws_titles = get_workshops(user_id=moderator,db=db)
    form = WorkshopsForm()
    form.workshop.choices = ws_titles

    if form.validate_on_submit() :
        name = form.name.data
        selected_w = form.workshop.data
        # test if open
        nowt = datetime.datetime.now(datetime.timezone.utc)
        reg_start = workshops[selected_w]['Regist. Start']
        reg_start = reg_start.replace(tzinfo=pytz.UTC)
        reg_end = workshops[selected_w]['Regist. End']
        reg_end = reg_end.replace(tzinfo=pytz.UTC)
        if reg_start  and nowt < reg_start:
            flash("Registration has not been started yet.\nStarting at {} (UTC)".format(reg_start.strftime("%Y-%m-%d, %H:%M")))
            return render_template('register.html', form=form)
        elif reg_end  and nowt > reg_end:
            flash("Registration is closed already.\nEnded at {} (UTC)".format(reg_end.strftime("%Y-%m-%d, %H:%M")))
            return render_template('register.html', form=form)
        else :
            info = workshops[selected_w]['Info']
            url = workshops[selected_w]['url']
            ws_title = workshops[selected_w]['Title']
            # test if user exist
            user_data = get_user(name,selected_w, db = db)
            if user_data :
                flash("User exists already - If you have not registered already choose another username.")
                return render_template('credentials.html',name = name,user= user_data[1], pwd = user_data[2],
                                       info = info,url = url,ws_title = ws_title)
            else:
                userpwd = create_user(name,selected_w,db=db)
                if not userpwd:
                    flash("No Users available anymore.")
                    return render_template('register.html', form=form)
                else:
                    return render_template('credentials.html',name = name,user= userpwd[0], pwd = userpwd[1],
                                           info = info,url = url,ws_title = ws_title,workshop_id = selected_w,moderator = moderator)

    return render_template('register.html', form = form)



if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
