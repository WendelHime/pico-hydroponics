import time
import machine

import dftds


class TDS:
    def __init__(self, tds_pin_number, transistor_pin_number, humidity_sensor, calibration_filepath='tds_calibration.json', adc_range=65535):
        self.transistor = machine.Pin(transistor_pin_number, machine.Pin.OUT)
        self.sensor = dftds.GravityTDS(
                tds_pin_number,
                adc_range=adc_range,
                k_value_repository=dftds.KValueRepositoryFlash(calibration_filepath))
        self.sensor.begin()
        self.transistor.off()
        self.humidity_sensor = humidity_sensor

    def collect_metric(self):
        self.transistor.on()
        time.sleep(0.1)
        resp = self.humidity_sensor.collect_metric()
        self.sensor.temperature = resp["temperature"]
        tds_value = self.sensor.update()
        self.transistor.off()
        time.sleep(0.1)
        return {"tds_value": tds_value}
