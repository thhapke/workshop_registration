import sdi_utils.gensolution as gs

import subprocess
import io
import logging
import os
import string
import secrets
import base64


try:
    api
except NameError:

    class api:

        queue = list()

        class Message:
            def __init__(self, body=None, attributes=""):
                self.body = body
                self.attributes = attributes

        def send(port, msg):
            api.queue.append(msg.body)


        class config:
            ## Meta data
            config_params = dict()
            version = "0.0.1"
            tags = {'': ''}
            operator_name = 'create_users'
            operator_description = "Create Users Credentials"
            operator_description_long = "Create User Credentials"

            num_users = 90
            config_params['num_users'] = {'title': 'Number of Users', 'description': 'Number of users', 'type': 'integer'}

            root_name = 'TED_'
            config_params['root_name'] = {'title': 'Root name', 'description': 'Root name for numbering', 'type': 'string'}

            pwd_length = 6
            config_params['pwd_length'] = {'title': 'Password Length', 'description': 'Password Length', 'type': 'integer'}

        logger = logging.getLogger(name='distribute_users')

# set logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
log_stream = io.StringIO()
sh = logging.StreamHandler(stream=log_stream)
#sh.setFormatter(logging.Formatter('%(asctime)s ;  %(levelname)s ; %(name)s ; %(message)s', datefmt='%H:%M:%S'))
api.logger.addHandler(sh)


def generate():

    # base set for pwd generation
    baseset = string.ascii_letters + string.digits
    baseset = [i for i in baseset if not i in 'Il0O']

    # User and pwd
    idx_users_pwd = [[str(i-1),api.config.root_name + str(i), ''.join(secrets.choice(baseset) for n in range(api.config.pwd_length))]
                 for i in range(1, api.config.num_users + 1)]
    #tenant = 'default'
    #idx_users_pwd_base64 = [[u[0],u[1],u[2],str(base64.b64encode('{}\\{}:{}'.format(tenant,u[0],u[1]).encode('ascii')))[2:-1]] for u in users_pwd]

    header = 'index,user,password\n'
    users_csv_str = header + '\n'.join([','.join(elem) for elem in idx_users_pwd])

    attributes = {"file": {"connection": {"configurationType": "Connection Management", "connectionID": ""},"path": "", "size": 0}}
    msg = api.Message(attributes=attributes,body=users_csv_str)
    api.send(outports[0]['name'],msg)


outports = [{'name': 'users', 'type': 'message.file',"description":"new user"}]

#api.add_generator(generate)


def test_operator() :

    api.config.num_users = 90
    api.config.root_name = 'ted_'
    api.config.pwd_length = 6

    filename = 'DAT262_2.csv'

    generate()

    with open(os.path.join("/Users/Shared/data/registration",filename), 'w') as file:
        for m in api.queue :
            file.write(m)


if __name__ == '__main__':

    test_operator()
    if True :

        basename = os.path.basename(__file__[:-3])
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        solution_name = '{}_{}'.format(basename,api.config.version)
        solution_dir = os.path.join(project_dir,'solution/operators',solution_name)
        solution_file = os.path.join(solution_dir,solution_name+'.zip')

        subprocess.run(["rm", '-r',solution_file])
        gs.gensolution(os.path.realpath(__file__), api.config, None, outports)

        subprocess.run(["vctl", "solution", "bundle", solution_dir, "-t", solution_file])
        subprocess.run(["mv", solution_file, os.path.join(project_dir,'solution/operators')])

