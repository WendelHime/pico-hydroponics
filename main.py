import time
import network

import machine
from machine import ADC, Pin
import uasyncio as asyncio
import ntptime

import dht
import dftds
import secret
import urequests
import ujson


HUMIDITY_POWER_PIN = 15
HUMIDITY_PIN = 14
PH_PIN = 28
TDS_PIN = 27

onboard_led = Pin("LED", Pin.OUT)
humidity_pin_power = Pin(HUMIDITY_POWER_PIN, Pin.OUT)
humidity_pin_power.on()
temperature_sensor = dht.DHT22(Pin(HUMIDITY_PIN))
ph_sensor = ADC(Pin(PH_PIN))
tds_sensor = dftds.GravityTDS(TDS_PIN, adc_range=65535, k_value_repository=dftds.KValueRepositoryFlash('tds_calibration.json'))
tds_sensor.begin()

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

# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
# (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 3155673600 if time.gmtime(0)[0] == 2000 else 2208988800

# The NTP host can be configured at runtime by doing: ntptime.host = 'myhost.org'
host = "pool.ntp.org"

def set_time(hrs_offset=0):  # Local time offset in hrs relative to UTC
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    try:
        addr = socket.getaddrinfo(host, 123)[0][-1]
    except OSError as ex:
        print(ex)
        return 0
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    poller = select.poll()
    poller.register(s, select.POLLIN)
    try:
        s.sendto(NTP_QUERY, addr)
        if poller.poll(1000):  # time in milliseconds
            msg = s.recv(48)
            val = struct.unpack("!I", msg[40:44])[0]  # Can return 0
            return max(val - NTP_DELTA + hrs_offset * 3600, 0)
    except OSError as ex:
        print(ex)
        pass  # LAN error
    finally:
        s.close()
    return 0  # Timeout or LAN error occurred

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
        print('ipconfig: ',status)

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

        ph_value = collect_ph()

        tds_sensor.temperature = temperature
        tds_value = tds_sensor.update()

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
