# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 17:07:06 2019

@author: JOANRR
"""
from ..resources import sourcemeter
from numpy import array

class agilentE3631A(sourcemeter):
    """This class uses the sourcemeter class to open a resource instance for power supply of type Agilent E3631A"""
    def __init__(self, resource):
        sourcemeter.__init__(self,resource)
        #print(self.identify[0:22])
        if ('E3631A' in self.identify):
            print('You have connected succesfully with a %s' % self.identify)
        else:
            raise  Exception('Not able to connect with a Agilent E3631A sourcemeter, instead : \n {}'.format(self.identify))
    def config_volt(self,voltage = 0.0, output = 'P6V'):
        """Configures the instrument for a DC voltage reading:
            - voltage = 0.0:  sets the voltage output to the desired level
            - output = 'P6V': sets the output source that will be configured (P6V, P25V or N25V)"""  
        self.inst.write('*RST')
        self.inst.write('INST {:}'.format(output))
        self.inst.write(':SOUR:VOLT {:.4f}'.format(voltage))
        self.output = output
    def set_volt(self,voltage):
        """Sets a new voltage, assuming it has already been configured"""
        self.inst.write(':SOUR:VOLT {:.4f}'.format(voltage))
        return None
    def outpon(self):
        """Turns on the instrument"""
        self.inst.write(":OUTPut ON")
    def outpstate(self):
        """Checks the output state"""
        return bool(self.inst.query_ascii_values(":OUTPut?")[0])
    def outpoff(self):
        """Turns off the instrument"""
        self.inst.write(":OUTPut OFF")
    def read_value(self, value = 'volt'):
        """Reads the voltage/current value, it could but more general, but it isn't right now
        it returns a list. Args:
        value = 'volt': reads the voltage or current (as 'curr')"""
        if value == 'volt':
            self.reading =  self.inst.query_ascii_values('MEAS:VOLT? ' + self.output, container=array)
        elif value == 'curr':
            self.reading =  self.inst.query_ascii_values('MEAS:CURR? ' + self.output, container=array)
        else:
            raise Exception('Specified value not known')
        return self.reading[0]
    