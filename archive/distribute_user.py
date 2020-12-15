
import csv


# Read file into list
users_file = "/Users/Shared/data/IoTquality/users.csv"
with open(users_file, newline='') as file:
    reader = csv.reader(file)
    users = list(reader)
header = users.pop(0)
print(users)

num_requests = 50
requests = ['req_'+str(i) for i in range(1,num_requests+1)]

# Request user
user_index = 0

for r in requests :
    if user_index >= len(users) :
        print('No user available anymore. Max users: {}'.format(len(users)))
        break
    users[user_index] = [users[user_index][0],users[user_index][1],r]
    print('New user: {}'.format(users[user_index]))
    user_index +=1