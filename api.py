from microdot import Microdot, Response

def build_ap_mode(calibration_logic):

    app = Microdot()
    Response.default_content_type = 'application/json'

    @app.post('/credentials')
    def credentials(request):
        request_body = request.json
        ssid = request_body['ssid']
        password = request_body['password']
        api_key = request_body['api_key']
        user_id = request_body['user_id']
        content = 'ssid, password, api_key, user_id = "{}", "{}", "{}", "{}"\n'.format(ssid, password, api_key, user_id)
        with open('config.py', mode='w') as f:
            f.write(content)
        return {'status': 'success'}, 200

    @app.post('/calibrate/tds/<path:buffer>')
    def calibrate_tds(request, buffer):
        k = calibration_logic.calibrate_tds(buffer)
        if k != 1.0:
            return {'k': k}, 200
        return {'status': 'failed to calibrate TDS'}, 500

    @app.get('/calibrate/ph/<path:buffer>')
    def read_ph(request, buffer):
        buffer_voltage = calibration_logic.read_ph(buffer)
        return {"ph_voltage": buffer_voltage, "buffer": buffer, "status": "ok"}, 200

    @app.post('/calibrate/ph')
    def calibrate_ph(request):
        m, b = calibration_logic.calibrate_ph()
        content = 'm, b = {}, {}'.format(m, b)
        with open('config.py', mode='a') as f:
            f.write(content)
        return {'m': m, 'b': b}, 200

    @app.post('/shutdown')
    def shutdown(request):
        request.app.shutdown()
        return {'status': "service shutting down"}

    return app
