from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

import requests
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'DI302020WSTed'

bootstrap = Bootstrap(app)
moment = Moment(app)

# restapi
url = 'https://vsystem.ingress.dh-ia37o5zq.dhaas-live.shoot.live.k8s-hana.ondemand.com/app/pipeline-modeler/openapi/service/teched2020/register/subscribe'
ra_user = 'teched2020'
ra_pwd = 'Ted2345!'

class NameForm(FlaskForm):
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
    form = NameForm()
    if form.validate_on_submit() :
        name = form.name.data
        status, resp = call_restapi(name)
        if status == 404:
            return render_template('notopen.html')
        else:
            if resp['status'] == 'notready' :
                return render_template('notready.html',ws_title = resp['title'])
            elif resp['status'] == 'nouser' :
                return render_template('nouser.html',ws_title = resp['title'])
            elif resp['status'] == 'exist' :
                return render_template('credentials_exist.html', name = resp['name'],user= resp['user'], pwd = resp['password'],
                                   b64 = resp['base64auth'],url = resp['url'],ws_title = resp['title'])
            else :
                return render_template('credentials.html',name = resp['name'],user= resp['user'], pwd = resp['password'],
                                   b64 = resp['base64auth'],url = resp['url'],ws_title = resp['title'])
    return render_template('diregister.html',form = form)

def call_restapi(name) :
    # send request
    auth = ('default\\' + ra_user, ra_pwd)
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    resp = requests.post(url, data=name, auth=auth, headers=headers)
    ret_data = None
    if resp.status_code == 200 :
        ret_data =  json.loads(resp.text)
    return resp.status_code, ret_data



if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)
