# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:45:45 2019

@author: JOANRR
"""

from ..resources import sourcemeter


class keysight33500B(sourcemeter):
    """This class uses the sourcemeter class to open a resource instance froa fucntion generator from type 33500B from Keysight / Agilent Technologies"""
    
    def __init__(self, resource):
        sourcemeter.__init__(self,resource)
        #Test to ensure you are connectic to the desired instrument, can gies problems if the name doesn't match,
        # in that case, just comment the while if/else statement
        if (self.identify[0:20] == "Agilent Technologies"):
            print('You have connected succesfully with a %s' % self.identify)
        else:
            raise  Exception('Not an Agilent Technologies family instrument, an instrument of type %s is detected' % self.identify)
    def quick_config(self, channel, function, freq, ampl, offset = 0.0):
        """It quickly configures the specified channel (1 or 2) for a waveform of the specified function (SINusoid | SQUare | TRIangle | RAMP | PULSe | PRBS | NOISe | ARB |
        DC, as a str) at the given frequency and amplitude.
        Optional argument:
            - offset: set to zero as default.
        """
        command = ':SOURce{:1d}:APPLy:{:s}  {:.6e},{:.6e},{:.6e}'.format(channel,function,freq, ampl, offset)
        #print(command)
        self.inst.write(command)
    def outpoff(self, channel):
        """Turns off the instrument."""
        self.inst.write(":OUTPut{:1d} OFF".format(channel))
    def outpon(self, channel):
        """Turns on the instrument."""
        self.inst.write(":OUTPut{:1d} ON".format(channel))
    def close(self):
        """Closes the resource instance."""
        self.inst.close()