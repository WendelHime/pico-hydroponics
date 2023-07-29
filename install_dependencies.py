import uasyncio
import mip

from local_network import std_network
import config

async def main():
    uasyncio.create_task(std_network.connect_to_network(config.ssid, config.password))
    with open("requirements.txt", "r") as f:
        content = f.read()
        requirements = content.split("\n")
        for req in requirements:
            mip.install(req)


try:
    uasyncio.run(main())
finally:
    uasyncio.new_event_loop()
