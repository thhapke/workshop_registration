import requests
import json

# restapi
url = 'https://vsystem.ingress.dh-ia37o5zq.dhaas-live.shoot.live.k8s-hana.ondemand.com/app/pipeline-modeler/openapi/service/teched2020/register/subscribe'
ra_user = 'teched2020'
ra_pwd = 'Ted2345!'

# send request
auth = ('default\\' + ra_user, ra_pwd)
headers = {'X-Requested-With': 'XMLHttpRequest'}
resp = requests.post(url, data='lol2', auth=auth, headers=headers)

print(resp.text)
data = json.loads(resp.text)
print(data)