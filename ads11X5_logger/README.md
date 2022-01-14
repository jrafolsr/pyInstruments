# photodiode
Code to read a photodiode current/voltage trought a ADS1115 microcontroller.

To hook up the ADS1115 follow the steps on:
https://learn.adafruit.com/raspberry-pi-analog-to-digital-converters/ads1015-slash-ads1115


which mainly summarize in:

ENABLE the I2C on the Raspberry Pi! (https://learn.adafruit.com/adafruits-raspberry-pi-lesson-4-gpio-setup/configuring-i2c):

1. SKIP the following two installation as they are already on the Raspberry Pi
	sudo apt-get install -y python-smbus
	sudo apt-get install -y i2c-tools

2. Follow the rest of the instructions.


