# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 16:50:51 2019

@author: JOANRR
"""
from ..resources import sourcemeter
from numpy import array

class keysight34461A(sourcemeter):
    """This class uses the sourcemeter class to open a resource instance for a multimeter
    of type 34401A or 34461A either from Hewlett Packard, Agilent or, later, from Keysight, 
    despite the name of the class"""
    def __init__(self, resource):
        sourcemeter.__init__(self,resource)
        #print(self.identify[0:21])
        if ('34461A' in self.identify) or ('34401A' in self.identify):
            print('You have connected succesfully with a %s' % self.identify)
        else:
            raise  Exception('Not able to connect with a 34461A multimeter, instead : \n {}'.format(self.identify))

    def config_temp(self, fw = True, units  = 'C', nplc = 1, count = 1):
        """Configures the instrument for a temperature reading:
            - fw = True: the 4-wire is enabled by default, if false the measurement is done in 2-w
            - units = 'C': can be either in Kelvin 'K' or Fahrenheit 'F' too, default is Celsius degrees
            - nplc = 10: number of light cycles in which the measurement is integrated
             - count = 1: number of measurements"""
        assert not ('34401A' in self.identify), 'The old 34401A does not have the TEMPERATURE reading command, proceed with voltage reading instead'
        self.inst.write('*RST')
        if fw:
            self.inst.write('CONF:TEMP FRTD')
            self.inst.write('UNIT:TEMP %1s' % units)
            self.inst.write('TEMP:NPLC %i' % nplc)
            self.inst.write('SAMPle:COUNt {:d}'.format(count))
        else:
            self.inst.write('CONF:TEMP RTD')
            self.inst.write('UNIT:TEMP %1s' % units)
            self.inst.write('TEMP:NPLC %.3f' % nplc)
            self.inst.write('SAMPle:COUNt {:d}'.format(count))
    def read(self):
        """Reads the configurated value, it could but more general, but it isn't right now
        it returns a list"""
        self.reading =  self.inst.query_ascii_values('READ?', container=array)
        return self.reading
    def config_volt(self,rang = 0.1, nplc = 1, count = 1):
        """Configures the instrument for a DC voltage reading:
            - nplc = 1: number of light cycles in which the measurement is integrated"""  
        self.inst.write('*RST')
        self.inst.write('CONF:VOLT:DC {:.6e}'.format(rang))
        self.inst.write('SENSe:VOLT:DC:NPLC {:.3f}'.format(nplc))
        self.inst.write('SAMPle:COUNt {:d}'.format(count))
        
    def config_ohms(self, fw = True,rang = 'DEF', nplc = 1, count = 1):
        """Configures the multimeter for a resistance measurement. Optional arguments are:
            - fw = True: the 4-wire is enabled by default, if false the measurement is done in 2-w
            - rang = 'DEF': set the rang of the measruement, 'DEF' leaves it as default / automatic
            - nplc = 10: number of light cycles in which the measurement is integrated
            - count = 1: number of measurements"""
        self.inst.write('*RST')
        if fw:
            self.inst.write('CONF:FRESistance {}'.format(rang))
            self.inst.write('FUNC "FRESistance"')
            self.inst.write('SENSe:FRES:NPLC {:.3f}'.format(nplc))
            self.inst.write('SAMPle:COUNt {:d}'.format(count))
        else:
            self.inst.write('CONF:RESistance {}'.format(rang))
            self.inst.write('FUNC "RESistance"')
            self.inst.write('SENSe:RES:NPLC {:.3f}'.format(nplc))
            self.inst.write('SAMPle:COUNt {:d}'.format(count))
    def outpoff(self):
        """Turns off the instrument"""
        self.inst.write(":OUTPut OFF")
    def close(self):
        """Closes the resource instance."""
        self.inst.close()

