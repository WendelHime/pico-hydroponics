import time
import machine


class WaterTemperature:
    def __init__(self, temperature_pin_number, transistor_pin_number):

        """
        WaterTemperature encapsulate temperature output functionality from the pH probe
        Args:
            temperature_pin_number: An integer value representing the temperature output (TO)
            transistor_pin_number: An integer value representing the transistor pin for turning on/off the module
        """
        self.temperature = machine.ADC(temperature_pin_number)
        self.transistor = machine.Pin(transistor_pin_number, machine.Pin.OUT)
        self.transistor.off()

    def collect_temperature_voltages(self):
        temperature_voltages = []
        for i in range(10):
            voltage = self.temperature.read_u16()
            temperature_voltages.append(voltage)
            time.sleep(0.1)
        return temperature_voltages

    def collect_metric(self):
        self.transistor.on()
        time.sleep(0.1)
        voltages = self.collect_temperature_voltages()
        avg_temperature_voltage = sum(voltages) / len(voltages)
        water_temperature = (avg_temperature_voltage/65535)*60
        self.transistor.off()
        time.sleep(0.1)
        return {"water_temperature": water_temperature}
