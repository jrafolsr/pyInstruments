# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 17:07:06 2019

@author: JOANRR
"""
from ..resources import sourcemeter
from numpy import array

class agilentE36XXA(sourcemeter):
    """ This class uses the sourcemeter class to open a resource instance for power supply of type Agilent E36xxA.
    In is highly simplified and thought to be used (so far) with the models E3631A (triple output) or E3647A"""
    def __init__(self, resource):
        sourcemeter.__init__(self,resource)
        identity = self.identify
        if ('HEWLETT-PACKARD,E36' in identity) | ('Agilent Technologies,E36' in identity):
            print('You have connected succesfully with a %s' % identity)
        else:
            raise  Exception('Not able to connect with a Agilent E3631A sourcemeter, instead : \n {}'.format(self.identify))
            
        if 'E3631A' in identity:
            self.model = 'triple'
        elif 'E3647A' in identity:
            self.model = 'dual'
            self.output = ''
        else:
            raise Exception('Power supply model not known.')

    def config_volt(self,voltage = 0.0, output = 'default'):
        """Configures the instrument for a DC voltage reading:
            - voltage = 0.0:  sets the voltage output to the desired level
            - output = 'default': sets the output source to the default, which is P25V for the E3631A or OUT1 for the ES3647A.
        """
        
        if output == 'default':
            if self.model == 'triple':
                output = 'P25V'
                self.output = output
            elif self.model == 'dual':
                output = 'OUT1'
                self.output = ''
        else:
            if self.model == 'triple':
                 self.output = output
            elif self.model == 'dual':
                 self.output = ''

        self.inst.write('*RST')
        self.inst.write('INST:SEL {}'.format(output))
        self.inst.write(':SOUR:VOLT {:.4f}'.format(voltage))
        
        
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
        if value is 'volt':
            self.reading =  self.inst.query_ascii_values('MEAS:VOLT? ' + self.output, container=array)
        elif value is 'curr':
            self.reading =  self.inst.query_ascii_values('MEAS:CURR? ' + self.output, container=array)
        else:
            raise(Error('Specified value not known'))
        return self.reading[0]
    