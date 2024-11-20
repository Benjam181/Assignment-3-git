import json
import configparser
import paho.mqtt.client as mqtt
from SQL import SQL
from datetime import datetime

class MQTT_config:
    def __init__(self, client_type, on_message_callback=None):
        """
        type can be Publisher and Subscriber (1) or Publisher (2)
        """
        # Initialize SQL database
        self.sql = None
        # if _connected == false, nothing happen.
        self.sql_connection = False
        
        # Initialize ConfigParser
        config = configparser.ConfigParser()
        config.read('config.ini')
        
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
        
        if client_type == 1:
            self.client.subscribe(self.PI_config_topic)
            self.client.on_message = self._on_message
            self.on_message_callback = on_message_callback  # RÃ©fÃ©rence Ã  la mÃ©thode de mise Ã  jour du graphique
        
        self.client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
        self.client.username_pw_set(username, password)
        self.client.connect(broker_address, port=port)
        self.client.loop_start()
        
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully")
            client.subscribe(self.PI_config_topic)

        else:
            print("Connect returned result code: " + str(rc))
    
    
    def _on_disconnect(self, client, userdata, rc):
        print(f"Disconnected, tentative de reconnexion. Code de retour {rc}")
        if rc != 0:
            # Try to reconnect
            client.reconnect()
            
    def _on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        print("Message Changed !")
                    
        if msg.topic == self.PI_config_topic:
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
        
   
