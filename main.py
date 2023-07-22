import time
import machine
import uasyncio as asyncio
import ntptime

import secret
import api
import logic
import ph
import tds
import humidity
import water_temperature
import std_network


HUMIDITY_POWER_PIN = 0
HUMIDITY_PIN = 1
PH_PIN = 28
PH_TEMP_PIN = 27
TDS_PIN = 26
TRANSISTOR_PH_PIN = 22
TRANSISTOR_TDS_PIN = 21


onboard_led = machine.Pin("LED", machine.Pin.OUT)

def get_serial_id():
    s = machine.unique_id()
    chars = []
    for b in s:
        h = hex(b)[2:]
        if len(h) == 1:
            h = '0' + h
        chars.append(h)
    serial_id = '-'.join(chars)
    return serial_id


def init_sensors():
    sensors = []
    humidity_sensor = humidity.HumiditySensor(HUMIDITY_POWER_PIN, HUMIDITY_PIN)
    sensors.append(humidity_sensor)
    sensors.append(tds.TDS(TDS_PIN, TRANSISTOR_TDS_PIN, humidity_sensor))
    sensors.append(ph.PHSensor(PH_PIN, TRANSISTOR_PH_PIN))
    sensors.append(water_temperature.WaterTemperature(PH_TEMP_PIN, TRANSISTOR_PH_PIN))
    return sensors

async def main():
    if not secret.ssid:
        # initialize ap mode
        print("Initializing AP mode for general settings/calibration")
        api.app.run()

    print('Connecting to network...')
    asyncio.create_task(std_network.connect_to_network())
    await asyncio.sleep(5)
    try:
        ntptime.timeout = 5
        ntptime.settime()
    except Exception as ex:
        print("failed to set time", ex)

    serial_id = get_serial_id()
    metrics_collector = logic.MetricsCollector(serial_id, secret.api_key, sensors=init_sensors())
    while True:
        onboard_led.on()
        print('Starting to collect metrics')
        asyncio.create_task(metrics_collector.collect_metrics())
        onboard_led.off()
        await asyncio.sleep(5)

try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
