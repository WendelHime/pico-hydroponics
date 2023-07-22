import time
import machine


class PHSensor:
    def __init__(self, ph_pin_number, transistor_pin_number, b=-4.852947599489467, a=23.73194905699139):
        """
        PHSensor encapsulate pH module functionalities
        Args:
            ph_pin_number: An integer value representing the pH output (PO)
            transistor_pin_number: An integer value representing the transistor pin for turning on/off the module
            b: An float value from the linear regression calibration
            a: An float value from the linear regression calibration
        """
        self.probe = machine.ADC(ph_pin_number)
        self.transistor = machine.Pin(transistor_pin_number, machine.Pin.OUT)
        self.transistor.off()
        self.b = b
        self.a = a


    def collect_ph_voltages(self):
        ph_voltages = []
        for i in range(10):
            voltage = self.probe.read_u16()
            ph_voltages.append(voltage)
            time.sleep(0.1)
        return ph_voltages

    def collect_metric(self):
        self.transistor.on()
        time.sleep(0.1)
        ph_voltages = self.collect_ph_voltages()
        self.transistor.off()
        time.sleep(0.1)
        avg_ph_voltage = sum(ph_voltages) / len(ph_voltages)
        # We're providing to the pH 5V
        ph_voltage = (avg_ph_voltage * 5 / 65535)
        # linear regression after calibrating ph probe
        ph_value = self.b*ph_voltage+self.a
        return {"ph_value": ph_value}
