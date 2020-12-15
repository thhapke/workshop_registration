import string
import secrets
import base64


num_user = 45
user_root = 'TE_'
tenant = 'default'


baseset = string.ascii_letters + string.digits
baseset = [ i for i in baseset if not i in 'Il0O']
print(baseset)

users = [[user_root + str(i),''.join(secrets.choice(baseset) for n in range(4))] for i in range(1,num_user+1)]

with open("/Users/Shared/data/IoTquality/users.csv",'w') as file :
    file.write(','.join(['user','pwd','base64auth','name']) + '\n')
    for u in users :
        up_str = tenant + '\\' + u[0] + ':' + u[1]
        b64cred = base64.b64encode(up_str.encode('ascii'))
        file.write(','.join(u) + ',' + str(b64cred)[2:-1] + ',\n')

print(users)