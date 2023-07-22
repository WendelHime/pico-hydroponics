import network

def build_ssid(serial_id):
    return "hydroponics-%s" % serial_id

def create_network(ssid, password):
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    print(ap.ifconfig())
    return ap

def stop_ap_mode(ap):
    ap.active(False)
