import time
from machine import Pin

import dht

class HumiditySensor:
    def __init__(self, power_pin_number, data_pin_number):
        self.humidity_power = Pin(power_pin_number, Pin.OUT)
        self.humidity_power.on()
        self.sensor = dht.DHT22(Pin(data_pin_number))

    def collect_metric(self):
        self.sensor.measure()
        temperature = self.sensor.temperature()
        humidity = self.sensor.humidity()
        return {"temperature": temperature, "humidity": humidity}
