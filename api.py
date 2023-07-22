import time
import network

from microdot import Microdot, Response

import secret

app = Microdot()
Response.default_content_type = 'application/json'

@app.route('/')
def index(request):
    return {'message':'hello world'}

@app.route('/shutdown')
def shutdown(request):
    request.app.shutdown()
    return {'status': "service shutting down"}

if __name__ == '__main__':
    app.run(debug=True)
