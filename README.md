# Workshop Registration

This application let you setup workshops and provides a registration page for workshop participants to retrieve their credentials. 
This avoids that at the beginning of a workshop the moderator had to hand the information to each participant manually. The
developement was triggered by the SAP TechEd2020 when all workshops went virtual. 

## Registration App
1. Landing page: Selecting a workshop and providing a name
2. Informational page with credentials, etc

## Admin App
1. **Overview** of all workshops
2. **Edit** the list of workshops (Change, add and remove)
3. **Generate** a user list for a workshop
4. **Monitoring** the registration of a workshop 

The data is stored currently in a HANA Cloud database and the HDBCLI-client is used to connect to the database. Although 
preferring kind of standards, SQLAlchemy was not used. Maybe in future I give it a try and use the 
[SQLAlchemy dialect for SAP HANA](https://github.com/SAP/sqlalchemy-hana/blob/master). In this case it would be easier to 
replace HANA with a another DB, for what no real reason exists ;). 

## To-Dos
* There is no authentication for the admin app, yet. This will be added when the next workshops are planned
* Currently all coding is in on file. If time is on hand then I will set a new order with Flask-Blueprints. 
 
   