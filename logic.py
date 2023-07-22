import service

class MetricsCollector:
    def __init__(self, sensor_id, api_key, sensors=[]):
        self.sensor_id = sensor_id
        self.api_key = api_key
        self.sensors = sensors

    async def collect_metrics(self):
        try:
            responses = {}
            for sensor in self.sensors:
                responses.update(sensor.collect_metric())

            metrics = parse_responses_to_request(responses, self.sensor_id)
            service.send_metrics(metrics, self.api_key)
        except Exception as ex:
            print("failed to acquire data", ex)

def parse_responses_to_request(responses, serial_id):
    return service.MetricsRequest(
            responses['ph_value'],
            responses['tds_value'],
            responses['temperature'],
            responses['humidity'],
            responses['water_temperature'],
            serial_id)

class Calibration:
    def __init__(self, ph_sensor, tds_sensor):
        self.ph_buffer_voltage = {}
        self.tds_buffer_voltage = {}
        self.ph_sensor = ph_sensor
        self.tds_sensor = tds_sensor

    def read_ph(self, buffer):
        ph_voltages = self.ph_sensor.collect_voltages()
        avg_ph_voltage = sum(ph_voltages) / len(ph_voltages)
        ph_voltage = (avg_ph_voltage * 5 / 65535)
        self.ph_buffer_voltage[buffer] = ph_voltage
        return self.ph_buffer_voltage[buffer]

    def calibrate_ph(self):
        buffers = list(self.ph_buffer_voltage.keys())
        buffers.sort()
        buffers.reverse()
        sorted_ph_buffer_voltage = {i: self.ph_buffer_voltage[i] for i in buffers}

        numerator = 0
        denominator = 0
        first_buffer = 0
        for buffer in sorted_ph_buffer_voltage:
            voltage = self.ph_buffer_voltage[buffer]
            if first_buffer == 0:
                voltage = self.ph_buffer_voltage[buffer]
                numerator = buffer
                denominator = voltage
                first_buffer = buffer
            numerator -= buffer
            denominator -= voltage
        m = numerator/denominator
        b = (m*sorted_ph_buffer_voltage[first_buffer])*-1
        self.ph_sensor.m = m
        self.ph_sensor.b = b
        return b, m

    def calibrate_tds(self, buffer):
        self.tds_sensor.transistor.on()
        self.tds_sensor.collect_metric()
        self.tds_sensor.sensor.calibrate(buffer)
        return self.tds_sensor.sensor.k_value
