import time
import network

import secret


async def connect_to_network():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm = 0xa11140)
    wlan.connect(secret.ssid, secret.password)
    max_wait = 10
    while max_wait > 0:
        wlan_status = wlan.status() 
        if wlan_status < 0 or wlan_status >= 3:
            break
        max_wait -= 1
        print('waiting for connection')
        time.sleep(1)
    wlan_status = wlan.status()
    if wlan.status() != 3:
        raise RuntimeError("network connection failed")
    print('connected', wlan_status)
    status = wlan.ifconfig()
    print('ipconfig: ',status)
