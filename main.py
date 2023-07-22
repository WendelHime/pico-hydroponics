import time
import network
import machine
from machine import ADC, Pin
import uasyncio as asyncio
import urequests
import ujson
import ntptime

import dht
import dftds

import secret


HUMIDITY_POWER_PIN = 15
HUMIDITY_PIN = 14
PH_PIN = 28
PH_TEMP_PIN = 27
TDS_PIN = 26
TRANSISTOR_PH_PIN = 0
TRANSISTOR_TDS_PIN = 1


onboard_led = Pin("LED", Pin.OUT)
humidity_pin_power = Pin(HUMIDITY_POWER_PIN, Pin.OUT)
humidity_pin_power.on()
temperature_sensor = dht.DHT22(Pin(HUMIDITY_PIN, Pin.IN))
ph_sensor = ADC(Pin(PH_PIN, Pin.IN))
ph_temp_sensor = ADC(Pin(PH_TEMP_PIN, Pin.IN))
tds_sensor = dftds.GravityTDS(TDS_PIN, adc_range=65535, k_value_repository=dftds.KValueRepositoryFlash('tds_calibration.json'))
tds_sensor.begin()
transistor_ph = Pin(0, Pin.OUT)
transistor_tds = Pin(1, Pin.OUT)
transistor_ph.off()
transistor_tds.off()

s = machine.unique_id()
chars = []
for b in s:
    h = hex(b)[2:]
    if len(h) == 1:
        h = '0' + h
    chars.append(h)
serial_id = '-'.join(chars)

wlan = network.WLAN(network.STA_IF)
wlan_status = 0
wlan_status_lock = asyncio.Lock()

async def connect_to_network():
    wlan.active(True)
    wlan.config(pm = 0xa11140)
    wlan.connect(secret.ssid, secret.password)
    
    max_wait = 10
    while max_wait > 0:
        async with wlan_status_lock:
            wlan_status = wlan.status() 
            if wlan_status < 0 or wlan_status >= 3:
                break
            max_wait -= 1
            print('waiting for connection')
            time.sleep(1)
    
    wlan_status = wlan.status() 
    if wlan.status() != 3:
        raise RuntimeError("network connection failed")
    else:
        print('connected', wlan_status)
        status = wlan.ifconfig()
        print('ipconfig: ', status)

async def blink_led():
    wlan_status = wlan.status() 
    while wlan_status != 3:
        async with wlan_status_lock:
            wlan_status = wlan.status() 
            if wlan_status != 3:
                onboard_led.toggle()
            time.sleep(0.5)
    onboard_led.on()

class MetricsRequest:
    def __init__(self, ph_value, tds_value, temperature, humidity, serial_id):
        self.ph = ph_value
        self.tds = tds_value
        self.ec = tds_value*2
        self.temperature = temperature
        self.humidity = humidity
        self.sensor_id = serial_id
        self.sensor_version = "0.0.1"
        self.alias = "alface 1"
        self.timestamp = time.time()

    def __repr__(self):
        return repr({"ph": self.ph, "tds": self.tds, "ec": self.ec, "temperature": self.temperature, "humidity": self.humidity, "sensor_id": self.sensor_id, "sensor_version": self.sensor_version, "alias": self.alias, "timestamp": self.timestamp})

    def __getstate__(self):
        return {"ph": self.ph, "tds": self.tds, "ec": self.ec, "temperature": self.temperature, "humidity": self.humidity, "sensor_id": self.sensor_id, "sensor_version": self.sensor_version, "alias": self.alias, "timestamp": self.timestamp}

    def __setstate__(self, state):
        self.__dict__.update(state)

async def collect_metrics():
    try:
        temperature_sensor.measure()
        temperature = temperature_sensor.temperature()
        humidity = temperature_sensor.humidity()
        print("temperature", temperature, "humidity", humidity)

        transistor_ph.off()
        time.sleep(0.1)
        transistor_tds.on()
        time.sleep(0.1)
        tds_sensor.temperature = temperature
        tds_value = tds_sensor.update()
        print("tds sensor", tds_value)

        transistor_tds.off()
        time.sleep(0.1)
        transistor_ph.on()
        time.sleep(0.1)
        ph_value = collect_ph()
        print("ph temp sensor", (ph_temp_sensor.read_u16()/65535)*60, "ph_value", ph_value)

        metrics = MetricsRequest(ph_value, tds_value, temperature, humidity, serial_id)
        send_metrics(metrics)
    except Exception as ex:
        print("failed to acquire data", ex)

def collect_ph_voltages(ph_sensor):
    ph_voltages = []
    for i in range(10):
        voltage = ph_sensor.read_u16()
        ph_voltages.append(voltage)
        time.sleep(0.1)
    return ph_voltages

def collect_ph():
    ph_voltages = collect_ph_voltages(ph_sensor)
    avg_ph_voltage = sum(ph_voltages) / len(ph_voltages)
    # We're providing to the pH 5V
    ph_voltage = (avg_ph_voltage * 5 / 65535)
    # linear regression after calibrating ph probe
    ph_value = -4.852947599489467*ph_voltage+23.73194905699139
    return ph_value

def collect_ph_temperature():
    temperature_voltages = []
    for i in range(10):
        voltage = ph_temp_sensor.read_u16()
        temperature_voltages.append(voltage)
        time.sleep(0.1)
    avg_temperature_voltage = sum(temperature_voltages) / len(temperature_voltages)
    # We're providing to the pH 5V
    temperature_voltage = (avg_temperature_voltage * 5 / 65535)
    return temperature_voltage

def send_metrics(metrics):
    data = ujson.dumps(metrics.__dict__)
    headers = {"Content-Type": "application/json", "x-api-key": secret.api_key}
    response = urequests.post('https://hydroponics-gateway-djqh2e23.ue.gateway.dev/metrics', headers=headers, data=data)
    if response.status_code != 200:
        print(response.text)
    response.close()

async def main():
    print('Connecting to network...')
    asyncio.create_task(connect_to_network())
    asyncio.create_task(blink_led())
    await asyncio.sleep(5)
    try:
        ntptime.timeout = 5
        ntptime.settime()
    except Exception as ex:
        print("failed to set time", ex)

    while True:
        print('Starting to collect metrics')
        asyncio.create_task(collect_metrics())
        await asyncio.sleep(5)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
