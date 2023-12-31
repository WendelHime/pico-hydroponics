import time
import machine
import uasyncio as asyncio

import api 
from logic import MetricsCollector, Calibration
from sensors import ph, tds, humidity, water_temperature
from local_network import ap_network, std_network


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
    serial_id = get_serial_id()
    sensors = init_sensors()

    try:
        __import__('config')
    except ImportError:
        # initialize ap mode
        print("Initializing AP mode for general settings/calibration")
        ssid = "hydroponics"
        password = serial_id
        print(ssid, password)
        ap = ap_network.create_network(ssid, password)

        from uQR import QRCode
        qr = QRCode()
        qr.add_data('WIFI:S:{};T:WPA;P:{};H:false;;'.format(ssid,password), optimize=0)
        print(qr.render_matrix())

        calibration_logic = Calibration(sensors[2], sensors[1])
        api.build_ap_mode(calibration_logic).run(debug=True)
        ap_network.stop_ap_mode(ap)
        await asyncio.sleep(1)
        machine.reset()

    import config

    #sensors[2].m = config.m
    #sensors[2].b = config.b

    print('Connecting to network...')
    print(config.ssid, config.password)
    asyncio.create_task(std_network.connect_to_network(config.ssid, config.password))
    await asyncio.sleep(5)
    try:
        import ntptime
        ntptime.timeout = 5
        ntptime.settime()
    except Exception as ex:
        print("failed to set time", ex)

    metrics_collector = MetricsCollector(serial_id, config.api_key, sensors=sensors)
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
