from microdot import Microdot, Response

class APModeAPI():

    app = Microdot()
    Response.default_content_type = 'application/json'

    def __init__(self, calibration_logic):
        self.calibration_logic = calibration_logic

    @app.post('/wlan')
    def credentials(self, request):
        request_body = request.json
        ssid = request_body['ssid']
        password = request_body['password']
        api_key = request_body['api_key']
        content = 'ssid, password, api_key = "{}", "{}", "{}"\n'.format(ssid, password, api_key)
        with open('config.py', mode='w') as f:
            f.write(content)
        return {'status': 'success'}, 200

    @app.post('/tds/<path:buffer>')
    def calibrate_tds(self, request, buffer):
        k = self.calibration_logic.calibrate_tds(buffer)
        if k != 1.0:
            return {'k': k}, 200
        return {'status': 'failed to calibrate TDS'}, 500

    @app.get('/ph/<path:buffer>')
    def read_ph(self, request, buffer):
        buffer_voltage = self.calibration_logic.read_ph(buffer)
        return {"ph_voltage": buffer_voltage, "buffer": buffer, "status": "ok"}, 200

    @app.post('/ph/')
    def calibrate_ph(self, request):
        m, b = self.calibration_logic.calibrate_ph()
        content = 'm, b = {}, {}'.format(m, b)
        with open('config.py', mode='a') as f:
            f.write(content)
        return {'m': m, 'b': b}, 200

    @app.post('/shutdown')
    def shutdown(self, request):
        request.app.shutdown()
        return {'status': "service shutting down"}

#if __name__ == '__main__':
#    APModeAPI().app.run(debug=True)
