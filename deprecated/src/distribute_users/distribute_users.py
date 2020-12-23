import sdi_utils.gensolution as gs

import subprocess
import io
import logging
import os
import json
import csv
from datetime import datetime
import base64


try:
    api
except NameError:

    class api:

        rqueue = list()
        uqueue = list()

        class Message:
            def __init__(self, body=None, attributes=""):
                self.body = body
                self.attributes = attributes

        def send(port, msg):
            if port == outports[1]['name'] :
                api.uqueue.append(msg.body)
            elif port == outports[2]['name'] :
                api.rqueue.append(msg.body)

        class config:
            ## Meta data
            config_params = dict()
            version = "0.0.1"
            tags = {'': ''}
            operator_name = 'distribute_users'
            operator_description = "Distribute Users"
            operator_description_long = "Distribute users via RestAPI"

            url = ''
            config_params['url'] = {'title': 'url','description': 'URL of the system','type': 'string'}

            tenant = 'default'
            config_params['tenant'] = {'title': 'Tenant','description': 'Tenant of DI system','type': 'string'}

            ws_title = ''
            config_params['ws_title'] = {'title': 'Workshop Title', 'description': 'Workshop title', 'type': 'string'}

            max_users = 10
            config_params['max_users'] = {'title': 'Maximum Users', 'description': 'Maximum users', 'type': 'integer'}

            user_offset = 0
            config_params['user_offset'] = {'title': 'User ID offset', 'description': 'User ID offset', 'type': 'integer'}

        logger = logging.getLogger(name='distribute_users')

# set logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log_stream = io.StringIO()
sh = logging.StreamHandler(stream=log_stream)
#sh.setFormatter(logging.Formatter('%(asctime)s ;  %(levelname)s ; %(name)s ; %(message)s', datefmt='%H:%M:%S'))
api.logger.addHandler(sh)



user_index = api.config.user_offset
users = list()
users_attributes = None

def on_users(msg):
    global user_index
    global users
    global users_attributes

    users_attributes = msg.attributes
    lines = msg.body.decode('utf-8').splitlines()
    users = list(csv.reader(lines))
    header = users.pop(0)

    api.send(outports[0]['name'], 'Read users: ' + str(users))


def on_request(msg):
    global user_index
    global users

    # prepare for a response message
    attributes = {}
    for key in msg.attributes:
        # only copy the headers that won't interfer with the recieving operators
        if not "openapi.header" in key or key == "openapi.header.x-request-key":
            attributes[key] = msg.attributes[key]

    # ensure that offset and max users are not larger than user list
    max_users = api.config.max_users + api.config.user_offset
    if max_users >= len(users) :
        max_users = len(users)

    user_name = msg.body.decode('utf-8')
    user_name_list = [u[3] for u in users[:user_index]]



    # test if user name already used
    try :
        index = user_name_list.index(user_name)
        base64auth = str(base64.b64encode('{}\\{}:{}'.format(api.config.tenant, users[index][1], users[index][2]).encode('ascii')))[2:-1]
        resp_dict = {"name": users[index][3], "user": users[index][1], "password": users[index][2],
                     "base64auth": base64auth, "registration_time": users[index][4], "url":api.config.url, "status":'exist',
                     "tenant":api.config.tenant,"title":api.config.ws_title}
        api.send(outports[2]['name'], api.Message(attributes=attributes, body=json.dumps(resp_dict)))
        return 0
    except ValueError:
        pass

    if len(users) == 0:
        api.send(outports[2]['name'], api.Message(attributes=attributes, body=json.dumps({'title':api.config.ws_title,'status':'notready'})))
        api.send(outports[0]['name'], 'Service not initialized yet.')
        return 0
    if user_index >= max_users:
        api.send(outports[2]['name'], api.Message(attributes=attributes,body=json.dumps({'title':api.config.ws_title,'status':'nouser'})))
        api.send(outports[0]['name'], 'No users available anymore (max:{} - user list length: {}).'.format(max_users,len(users)))
        return 0


    ######## outport messages

    ### response
    users[user_index].append(user_name)
    users[user_index].append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    base64auth = str(
        base64.b64encode('{}\\{}:{}'.format(api.config.tenant, users[user_index][1], users[user_index][2]).encode('ascii')))[2:-1]
    resp_dict = {"name": users[user_index][3], "user": users[user_index][1], "password": users[user_index][2],
                 "base64auth": base64auth, "registration_time": users[user_index][4], "url":api.config.url,
                 "tenant":api.config.tenant,"title":api.config.ws_title,"status":'new'}
    api.send(outports[2]['name'], api.Message(attributes=attributes, body=json.dumps(resp_dict)))

    ### new user
    csv_str = ','.join(users[user_index]) +  '\n'
    api.send(outports[1]['name'], api.Message(attributes=users_attributes, body=csv_str))

    ### logging
    api.send(outports[0]['name'],'{} -> user: {} password: {}  base64auth: {}  date: {}'.format(users[user_index][3], users[user_index][0],
                                                                                                users[user_index][1], users[user_index][2],
                                                                                                users[user_index][4]))

    user_index += 1


inports = [{'name': 'users', 'type': 'message.file', "description":"User csv with header"},
           {'name': 'request', 'type': 'message', "description":"Request"}]
outports = [{'name': 'log', 'type': 'string',"description":"logging"}, \
            {'name': 'newuser', 'type': 'message.file',"description":"new user"},
            {'name': 'response', 'type': 'message',"description":"response"}]

#api.set_port_callback("request", on_request)
#api.set_port_callback("users", on_users)


def test_operator() :

    api.config.max_users = 10
    api.config.tenant = 'default'
    api.config.url = "di.url.com/index"
    api.config.user_offset = 0

    users_file = "/Users/Shared/data/registration/DAT163_1.csv"
    users_data = open(users_file, mode='rb').read()
    msg = api.Message(attributes={'content' : 'users'}, body=users_data)
    on_users(msg)

    num_requests = 6
    requests = ['Anna','Berta','Cindy','Dora','Cindy','Emily','Fiona','Gertrude']

    for r in requests :
        msg = api.Message(attributes={'content' : 'requests'},body = r.encode('utf-8'))
        on_request(msg)

    for rm in api.rqueue :
        print(rm)
    for um in api.uqueue:
        print(um)

if __name__ == '__main__':

    test_operator()
    if True :

        basename = os.path.basename(__file__[:-3])
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        solution_name = '{}_{}'.format(basename,api.config.version)
        solution_dir = os.path.join(project_dir,'solution/operators',solution_name)
        solution_file = os.path.join(solution_dir,solution_name+'.zip')

        subprocess.run(["rm", '-r',solution_file])
        gs.gensolution(os.path.realpath(__file__), api.config, inports, outports)

        subprocess.run(["vctl", "solution", "bundle", solution_dir, "-t", solution_file])
        subprocess.run(["mv", solution_file, os.path.join(project_dir,'solution/operators')])

