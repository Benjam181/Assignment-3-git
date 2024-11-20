# Purpose of the project
The aim of this project is to create an airHeater controller interface. Here is a picture of the air heater.
<img width="806" alt="Air_heater" src="https://github.com/user-attachments/assets/8b133901-0bfc-42ba-91df-c66816720ad9">

A python program is running on a raspberry pi, while a GUI python script is running on the user laptop. On the GUI, the first thing the user has to do is connect to the SQL server. When he is logged in, the user may see the direct temperature and output voltage values being plotted. He also can change the PI settings and the reference value. The data transit from the raspberry pi to the GUI using MQTT. Every time a data is received in the GUI, it is sent to the SQL database. Using the third application, a web application, it is possible, after logged in, to see the data registered in the SQL database with a chart. The user can select the start and end times for plotting the data.
# How to use it
- Put the Control_app_raspberry.py, and a copy of the controllers and MQTT_config libraries in a raspberry pi.
- Add a config.ini. This file should have those parameters:
```config.ini
[MQTT]
broker_address = xxx
port = xxx
username = xxx
password = xxx

[FLASK]
secret_key = xxx
```
- Connect the raspberry pi to the air heater using the wiring sketch:
<img width="627" alt="Wiring" src="https://github.com/user-attachments/assets/2bd715cb-b8f1-42ef-b0cb-f781fab954a4">

- Run the code on the raspberry pi.
- Run the GUI code to see the data uploading
- When you are done with the temperature reading, you can see all the data plotted in the Web app.

# Connection to the database
To connect to the database in the GUI and the web app, you can use those username and password:
- username: admin,
- password: admin.

# Website
You may get more information about the project on this blog:
https://web01.usn.no/~271376/
