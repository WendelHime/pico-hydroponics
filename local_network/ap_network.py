import time
import network

def create_network(ssid, password):
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    max_wait = 10
    while max_wait > 0:
        ap_status = ap.status() 
        if ap_status < 0 or ap_status >= 3:
            break
        max_wait -= 1
        print('waiting for connection')
        time.sleep(1)
    print(ap.ifconfig())
    return ap

def stop_ap_mode(ap):
    ap.active(False)
