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
