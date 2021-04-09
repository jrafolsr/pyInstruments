# pyInstruments
[![MIT license](http://img.shields.io/badge/license-MIT-yellowgreen.svg)](http://opensource.org/licenses/MIT)

Pyhton library to control several lab scientific equipment such as sourcemeters, multimeters or daqs. It makes use of [pyvisa](https://pyvisa.readthedocs.io/en/latest/) allowing the creation of your own lab instruments(sweep current-voltage programs, data loggers, controllers, etc).

# The basic instrument classes

At the moment, only the following instruments can be controlled with minimal options each of it (turn on/off, few configuration possibilities and basic measurements).

- Keithley 24XX sourcemeter.
- Agilent E3631A and E3647A power supplies (dual and triple, respectively).
- Keysight 33500B function generator.
- Agilent/Hewlett Packard/Keysight 34401A and 34461A multimeters.
- Keithley 2182A Nanovoltmeter.
- National Instrument USB DAQ.

# Instrument examples

The folders [ivlogger](ivlogger) and [pid](pid) contain two examples of higher level instruments, where one or more of the basic instruments classes have been combined to create a scientific instrument to be used in the lab. 

- The [ivlogger](ivlogger) allows to configure a Keithley 2400 to supply a constant current/voltage while measuring the voltage/current. A graphical user interface using the [dash](https://dash.plotly.com/) framework is also provided by executing [IV_GUI](IV_GUI).

- The [pid](pid) contains a proportional-integral-derivative algorithm that can be use to control the action given to a system. On top of that, the [pid_GUI](pid/pid_GUI.py) and [pid_controls](pid/pid_controls.py) provide a example of usage: an intrument that controls the temperature of a thermoelectric Peltier cell. The temperature is read using an Agilent 34461A multimeter while an Agilent 34401A power supply is use to power the Peltier cell. The program can be run through its [GUI](pid/pid_GUI.py).

# (In preparation) Installation & documentation

At the moment the code is a bit messy, but I'm planning to put some order so it can be re-used in a more user-firendly way.