# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:58:09 2019

@author: JOANRR
"""
from ..resources import sourcemeter
from numpy import array


class nanovoltmeter(sourcemeter):
    """This class uses the sourcemeter class to open a resource instance for the two-channel Model 2182A Nanovoltmeter from Keithley. Not fully developed."""
    def __init__(self, resource):
        """Initiates the class with the resource name"""
        sourcemeter.__init__(self,resource)
        #print(self.identify[0:20])
        if (self.identify[0:36] == "KEITHLEY INSTRUMENTS INC.,MODEL 2182"):
            print('You have connected succesfully with a %s' % self.identify)
        else:
            raise  Exception('Not an Agilent Technologies family instrument')
    def quick_config(self, channel = 1, nplc = 1, rang = 0.1):
        """Quickly configures the measurement"""
        self.inst.write("*RST")                
        self.inst.write(":SENS:FUNC 'VOLT'")   
        self.inst.write(":SENS:CHAN {:d}".format(channel))
        self.inst.write(":SENSe:VOLTage:NPLCycles {:.1f}".format(nplc)) 
        self.inst.write(":SENSe:VOLTage:CHANne1l:RANGe {:.2f}".format(rang))
    def read(self):
        """Reads the value for whih it has been configured"""
        self.reading =  self.inst.query_ascii_values('READ?', container=array)
        return self.reading
    def close(self):
        """Closes the resource instance."""
        self.inst.close()