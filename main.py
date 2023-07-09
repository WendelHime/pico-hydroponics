import time
import network

from machine import ADC, Pin
import uasyncio as asyncio

import dht
import dftds
import secret
import urequests

class MetricsRequest:
    def __init__(self, ph_value, tds_value, temperature, humidity):
        self.ph_value = ph_value
        self.tds_value = tds_value
        self.ec = tds_value*2
        self.temperature = temperature
        self.humidity = humidity


def collect_ph_voltages(ph_sensor):
    ph_voltages = []
    for i in range(10):
        voltage = ph_sensor.read_u16()
        ph_voltages.append(voltage)
        time.sleep(0.1)
    return ph_voltages


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

async def collect_metrics():
    try:
        temperature_sensor.measure()
        temperature = temperature_sensor.temperature()
        humidity = temperature_sensor.humidity()
        print("Temperature: {}C Humidity: {:.0f}% ".format(temperature, humidity))

        ph_value = collect_ph()

        tds_sensor.temperature = temperature
        tds_value = tds_sensor.update()
        print("TDS: {}ppm, EC: {} mS/cm".format(tds_value, tds_value*2))

        request = MetricsRequest(ph_value, tds_value, temperature, humidity)
        #urequests.post('', )
    except Exception as ex:
        print("failed to acquire data", ex)

def collect_ph():
    ph_voltages = collect_ph_voltages(ph_sensor)
    avg_ph_voltage = sum(ph_voltages) / len(ph_voltages)
    # We're providing to the pH 3V
    ph_voltage = avg_ph_voltage * 3 / 65535
    # linear regression after calibrating ph probe
    ph_value = -4.25373*ph_voltage+17.28164
    print("PH Voltage: {}V, avg voltages: {}, estimated PH {} ".format(ph_voltage, avg_ph_voltage, ph_value))
    return ph_value

async def main():
    print('Connecting to network...')
    asyncio.create_task(connect_to_network())
    asyncio.create_task(blink_led())
    await asyncio.sleep(5)

    while True:
        print('Starting to collect metrics')
        asyncio.create_task(collect_metrics())
        await asyncio.sleep(5)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
