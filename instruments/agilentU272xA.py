# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 17:07:06 2019

@author: JOANRR
"""
import usbtmc
from numpy import array


class agilentU272xA():
    """ This class uses the sourcemeter class to open a resource instance for power supply of type Agilent E36xxA.
    In is highly simplified and thought to be used (so far) with the models E3631A (triple output) or E3647A"""
    def __init__(self, resource):
        self.inst = usbtmc.Instrument(resource)
        self.inst.write('*CLS; *RST')
        identity = self.inst.ask('*IDN?')
        if (('U272' in identity.split(',')[1]) & ('AGILENT' in identity.split(',')[0]) ):
            print('You have connected succesfully with a %s' % identity)
        else:
            raise  Exception('Not able to connect with a Agilent U272xA SMU, instead : \n {}'.format(identity))
            
        self.current_range = ['R1uA', 'R10uA', 'R100uA', 'R1mA', 'R10mA', 'R120mA']
        self.voltage_range = ['R2V', 'R20V']
        
        
    def configurate(self, value, channels, mode = 'CV', vrange = '20V', crange = '10mA', compliance = '120mA', nplc = 1):
        """
        
        Current goes in A
        """       
        channels = [channels] if not isinstance(channels, list) else channels

        values = [value] * len(channels) if  not isinstance(value, list) else value
        modes = [mode.upper()] * len(channels) if not isinstance(mode, list) else mode
        vranges = [vrange] * len(channels) if not isinstance(vrange, list) else vrange
        cranges = [crange] * len(channels) if not isinstance(crange, list) else crange
        compliances = [compliance] * len(channels) if not isinstance(compliance, list) else compliance
        
        config_str = ''
        
#        print(len(channels), len(values), len(modes), len(vranges), len(cranges), len(compliances))
        for v, ch, md, vrg,crg, cmpl in zip(values, channels, modes, vranges,cranges, compliances):
            if (md == 'CC' and cmpl[-1] == 'A') or  (md == 'CV' and cmpl[-1] == 'V') :
                self.close()
                raise ValueError('The mode and compliance must have complementary units (V/A)')
            
            config_str += 'SENS:CURR:NPLC {:d},(@{:d})\n'.format(nplc, ch)
            config_str += 'SENS:VOLT:NPLC {:d},(@{:d})\n'.format(nplc, ch)
            config_str += 'SOUR:VOLT:RANG {:s},(@{:d})\n'.format(vrg if vrg[0] == 'R' else 'R' + vrg, ch)
            config_str += 'SOUR:CURR:RANG {:s},(@{:d})\n'.format(crg if crg[0] == 'R' else 'R' + crg, ch)
            
            if md == 'CV':
                config_str += 'CURR:LIM {},(@{:d})\n'.format(cmpl, ch)
                config_str += 'VOLT {:.6f},(@{:d})\n'.format(v, ch)
            elif md =='CC':              
                config_str += 'VOLT:LIM {},(@{:d})\n'.format(cmpl, ch)
                config_str += 'CURR {:.6f},(@{:d})\n'.format(v, ch)
            else:
                raise TypeError('The input mode must be "CV" or "CC"')
        
        self.inst.write(config_str)
        
        return config_str
        
    def set_volt(self,voltage, channel):
        """Sets a new voltage, assuming it has already been configured"""
        self.inst.write('VOLT {:.6f},(@{:d})\n'.format(voltage, channel))

    def set_current(self, current, channel):
        """
        Sets the current in A
        """
        self.inst.write('CURR {:.6f},(@{:d})\n'.format(current, channel))
        
    def reset(self):
        """
        Resets the instrument
        """
        self.inst.write('*CLS; *RST')
    
    def outpon(self, channels):
        """
        Turns on the instrument for the spcified channels
        """
        channels = [channels] if isinstance(channels, int) else channels
        for channel in channels:
            self.inst.write('OUTPut ON, (@{:d})'.format(channel))
    
    def outpstate(self, channel):
        """
        Checks the output state
        """
        state = self.inst.ask('OUTP? (@{:d})'.format(channel))
        
        return state
    
    def outpoff(self, channels):
        """
        Turns off the output for the specified channels"""
        """Turns on the instrument"""
        channels = [channels] if isinstance(channels, int) else channels
        for channel in channels:
            self.inst.write('OUTPut OFF, (@{:d})'.format(channel))
        
    def read_values(self, channels):
        """
        Reads the current and voltage for the specified channels
        """
        channels = [channels] if not isinstance(channels, list) else channels
        
        output = []
        
        for ch in channels:
            voltage = float(self.inst.ask('MEAS:VOLT? (@{:d})'.format(ch)))
            current = float(self.inst.ask('MEAS:CURR? (@{:d})'.format(ch)))
            output.append(array([voltage, current]))
        return output
    
    def close(self):
        """
        Closes the resource
        """
        self.inst.close()