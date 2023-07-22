import time

import ujson
import urequests


class MetricsRequest:
    def __init__(self, ph_value, tds_value, temperature, humidity, water_temperature, serial_id):
        self.ph = ph_value
        self.tds = tds_value
        self.ec = tds_value*2
        self.temperature = temperature
        self.humidity = humidity
        self.water_temperature = water_temperature
        self.sensor_id = serial_id
        self.sensor_version = "0.0.1"
        self.alias = "alface 1"
        self.timestamp = time.time()

    def __repr__(self):
        return repr({"ph": self.ph, "tds": self.tds, "ec": self.ec, "temperature": self.temperature, "humidity": self.humidity, "water_temperature": self.water_temperature, "sensor_id": self.sensor_id, "sensor_version": self.sensor_version, "alias": self.alias, "timestamp": self.timestamp})

    def __getstate__(self):
        return {"ph": self.ph, "tds": self.tds, "ec": self.ec, "temperature": self.temperature, "humidity": self.humidity, "water_temperature": self.water_temperature, "sensor_id": self.sensor_id, "sensor_version": self.sensor_version, "alias": self.alias, "timestamp": self.timestamp}

    def __setstate__(self, state):
        self.__dict__.update(state)


def send_metrics(metrics, api_key):
    data = ujson.dumps(metrics.__dict__)
    headers = {"Content-Type": "application/json", "x-api-key": api_key}
    response = urequests.post('https://hydroponics-gateway-djqh2e23.ue.gateway.dev/metrics', headers=headers, data=data)
    if response.status_code != 200:
        print(response.text)
    response.close()
