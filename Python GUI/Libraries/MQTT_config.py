import json
import configparser
import paho.mqtt.client as mqtt
from Libraries.SQL import SQL
from datetime import datetime

class MQTT_config:
    def __init__(self, type, on_message_callback=None):
        """
        type can be raspberry or laptop
        """
        try:
            # Initialize ConfigParser
            config = configparser.ConfigParser()
            config.read('../config.ini')
            
            # Retrieve MQTT settings
            broker_address = config['MQTT']['broker_address']
            port = int(config['MQTT']['port'])
            username = config['MQTT']['username']
            password = config['MQTT']['password']
            
            self.airHeater_topic = "my/raspberry/airHeater"
            self.PI_config_topic = "my/raspberry/PI_config"
            
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            
            if type == 'laptop':
                # Initialize SQL database
                self.sql = None
                # if _connected == false, nothing happen.
                self.sql_connection = False
            elif type == 'raspberry':
                pass
            else:
                raise ValueError(f"Invalid mqtt_config type: {type}. Type must be 'raspberry' or 'laptop'")
                
            self.client.on_message = self._on_message
            self.on_message_callback = on_message_callback  # Référence à la méthode de mise à jour du graphique
            
            self.client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
            self.client.username_pw_set(username, password)
            self.client.connect(broker_address, port=port)
            self.client.loop_start()
            
        except ValueError as e:
            print(f"Error: {e}")
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully")
            if self.type == 'laptop':
                client.subscribe(self.airHeater_topic)
            elif self.type == 'raspberry':
                client.subscribe(self.PI_config_topic)

        else:
            print("Connect returned result code: " + str(rc))
    
    
    def _on_disconnect(self, client, userdata, rc):
        print(f"Disconnected, tentative de reconnexion. Code de retour {rc}")
        if rc != 0:
            # Try to reconnect
            client.reconnect()
            
    def _on_message(self, client, userdata, msg):
        if self.sql_connection == True:
            payload = msg.payload.decode('utf-8')
            print("Message Received !")
                
            if msg.topic == self.airHeater_topic:
                data = json.loads(payload)
                
                temperature = data.get("temperature")
                output = data.get("output")
                time = data.get("time")
                target = data.get("target")
                
                # Sending data on SQL db
                if self.sql == None:
                    self.sql = SQL() # The object is created here because of thread errors
                    
                        # Find Date and Time
                now = datetime.now()
                datetimeformat = "%Y-%m-%d %H:%M:%S"
                MeasurementDateTime = now.strftime(datetimeformat)
                
                self.sql.insert_data(temperature, output, target, MeasurementDateTime)
                
                if self.on_message_callback:
                    try:
                        self.on_message_callback(temperature, output, time, target)
                    except Exception as e:
                        print(f"Error when updating the chart : {e}")
                        
            elif msg.topic == self.PI_config_topic:
                data = json.loads(payload)
                
                reference = data.get("reference")
                Kp = data.get("Kp")
                Ti = data.get("Ti")
                
                if self.on_message_callback:
                    try:
                        self.on_message_callback(reference, Kp, Ti)
                    except Exception as e:
                        print(f"Error when changing the PI settings : {e}")
            
    def send_data(self, temperature, output, time, target):
        data = {
        "temperature": temperature,
        "output": output,
        "time": time,
        "target": target
        }
    
        message = json.dumps(data)
    
        self.client.publish(self.airHeater_topic, message)
        print("Data sent !")
        
    def send_PI_configuration(self, reference, Kp, Ti):
        data = {
            "reference": reference,
            "Kp": Kp,
            "Ti": Ti
        }
        
        message = json.dumps(data)
        
        self.client.publish(self.PI_config_topic, message)
        
   