import spidev
import time
from gpiozero import MCP3002
from Controllers import controllers
from MQTT_config import MQTT_config

class Control_app_raspberry:
    def __init__(self):
        # MQTT configuration
        self.mqtt_client = MQTT_config(client_type='raspberry', on_message_callback=self._change_PI_settings) # Type 1 means it is a publisher ans subscriber client

        # Initialize the MCP3002 ADC on SPI bus 1
        self.adc = MCP3002(channel=0, clock_pin=11, mosi_pin=10, miso_pin=9, select_pin=7)

        # Initialize the SPI interface for the MCP4911 DAC on SPI bus 0
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # SPI bus 0, chip select 0
        self.si.max_speed_hz = 1000000  # Set SPI speed to 1 MHz
        
        self.reference = 30 # degre C
        self.controller = controllers(r=self.reference)
        self.Kp = 1.11
        self.Ti = 12
        self.ts = 0.1 # s
        self.t = 0 # s

    def _set_dac_voltage(self, value):
        """
        Sends a voltage value to the MCP4911 DAC.
        The value should be between 0 and 5 (10-bit range).
        """
        if value < 0 or value > 5:
            raise ValueError("Value must be between 0 and 5")
        
        # Convert voltage to bit value
        print(f"Voltage = {value}")    
        value = value * 1023/5
        print(f"Bit = {value} (float)")
        value = int(value)
        print(f"Bit = {value} (int)")    
        # Construct the 16-bit command word for the MCP4911
        command = 0b0011 << 12 | (value & 0x3FF) << 2
        # Send command in two bytes (MSB first, then LSB)
        self.spi.xfer2([(command >> 8) & 0xFF, command & 0xFF])
    
    def _temperature_measurement(self):
        adc_value = self.adc.value
        voltvalue = adc_value * 5
        temp_value = (voltvalue - 1) * (50 - 0)/(5 - 1); # Convert to degrees
        temp_value = round(temp_value, 3)
        return temp_value

    def change_PI_settings(self, reference, Kp, Ti):
        self.reference = reference
        self.controller.r = reference
        self.Kp = Kp
        self.Ti = Ti
        print('data received')

    def main_loop(self):
        try:
            # Loop to read ADC values and set corresponding DAC voltage
            i = 0
            while True:
                temp = self._temperature_measurement()
                temp = self.controller.lowPass_filter(temp)
                print(f"Temperature Value: {temp} °C")
                print(f"ref value: {self.reference} °C")
                
                u = self.controller.PI_controller(input=temp, Kc=self.Kp, Ti=self.Ti)
                self._set_dac_voltage(u)
                
                self.t = self.t + self.ts
                
                # MQTT Publish
                self.mqtt_client.send_data(temp, u, self.t, self.reference)

                # Wait briefly between readings
                time.sleep(self.ts)

        except KeyboardInterrupt:
            print("Exiting program.")

        finally:
            # Clean up SPI connection
            self.spi.close()

if __name__ == "__main__":
    control_app_raspberry = Control_app_raspberry()
    control_app_raspberry.main_loop()
