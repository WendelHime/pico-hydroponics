AMPY_PORT = /dev/ttyACM0

sync:
	ampy -p $(AMPY_PORT) put local_network
	ampy -p $(AMPY_PORT) put sensors
	ampy -p $(AMPY_PORT) put services
	ampy -p $(AMPY_PORT) put api.py
	ampy -p $(AMPY_PORT) put logic.py
	ampy -p $(AMPY_PORT) put main.py

deps:
	ampy -p $(AMPY_PORT) run install_dependencies.py

run:
	ampy -p $(AMPY_PORT) run main.py --no-output

.PHONY: run deps sync
