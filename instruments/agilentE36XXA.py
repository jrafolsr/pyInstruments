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
        if value == 'volt':
            self.reading =  self.inst.query_ascii_values('MEAS:VOLT? ' + self.output, container=array)
        elif value == 'curr':
            self.reading =  self.inst.query_ascii_values('MEAS:CURR? ' + self.output, container=array)
        else:
            raise Exception('Specified value not known')
        return self.reading[0]
    
    
    def config_bipolar(self, voltage=0.0, current_limit_p6v=1.0, current_limit_p25v=1.0):
        """Configure P6V and P25V channels for bipolar Peltier drive via bridge wiring.
    
        E3631A wiring (do this ONCE on the bench, then leave it):
            P6V(–) ──── tied to ──── P25V(–)     <- floating midpoint;
                                                     MUST NOT be connected to
                                                     chassis, earth, or any
                                                     external ground.
            Peltier sits between P6V(+) and P25V(+).
    
        Operation:
            voltage > 0  -> P6V at |V|, P25V at 0
                            -> current from P6V(+) to P25V(+)
            voltage < 0  -> P6V at 0,   P25V at |V|
                            -> current from P25V(+) to P6V(+)
    
        On the E3631A, OUTP enables/disables all three channels together; there
        is no per-channel enable. The -25V channel is left at its *RST default
        (0 V, 1 A limit) and is not used by the bridge.
    
        Current limits are per-channel because the two channels have different
        ratings (P6V: 5 A; P25V: 1 A).
        """
        if self.model != 'triple':
            raise Exception('Bipolar mode requires the triple-output E3631A.')
        self.inst.write('*RST')
        self.inst.write('INST:SEL P6V')
        self.inst.write(f'SOUR:CURR {current_limit_p6v:.4f}')
        self.inst.write('SOUR:VOLT 0')
        self.inst.write('INST:SEL P25V')
        self.inst.write(f'SOUR:CURR {current_limit_p25v:.4f}')
        self.inst.write('SOUR:VOLT 0')
        self.output = 'bipolar'
        self.set_volt_bipolar(voltage)

    def set_volt_bipolar(self, voltage):
        """Apply a signed voltage to the Peltier via the P6V/P25V bridge.
    
        Always parks the inactive channel at exactly 0 V before raising the
        active one, so the two supplies never fight each other through zero.
        """
        if voltage >= 0:
            # Park P25V, then drive P6V
            self.inst.write('INST:SEL P25V')
            self.inst.write('SOUR:VOLT 0')
            self.inst.write('INST:SEL P6V')
            self.inst.write(f'SOUR:VOLT {voltage:.4f}')
        else:
            # Park P6V, then drive P25V
            self.inst.write('INST:SEL P6V')
            self.inst.write('SOUR:VOLT 0')
            self.inst.write('INST:SEL P25V')
            self.inst.write(f'SOUR:VOLT {abs(voltage):.4f}')
    
    def outpon_bipolar(self):
        """Enable outputs. On the E3631A this enables all three channels."""
        self.inst.write('OUTP ON')
    
    def outpoff_bipolar(self):
        """Disable outputs."""
        self.inst.write('OUTP OFF')
    
    def outpstate_bipolar(self):
        """Return True if outputs are enabled. Same as outpstate() on E3631A."""
        return bool(self.inst.query_ascii_values('OUTP?')[0])
    
    def read_value_bipolar(self, value='volt'):
        """Read signed voltage or current across the Peltier.
    
        Returns positive when P6V drives, negative when P25V drives.
        """
        if value == 'volt':
            v_p6 = self.inst.query_ascii_values('MEAS:VOLT? P6V')[0]
            v_p25 = self.inst.query_ascii_values('MEAS:VOLT? P25V')[0]
            return v_p6 - v_p25
        elif value == 'curr':
            i_p6 = self.inst.query_ascii_values('MEAS:CURR? P6V')[0]
            i_p25 = self.inst.query_ascii_values('MEAS:CURR? P25V')[0]
            # The active channel carries the meaningful current
            return i_p6 if abs(i_p6) > abs(i_p25) else -i_p25
        else:
            raise Exception('Specified value not known')