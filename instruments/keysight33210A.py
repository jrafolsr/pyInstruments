# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:45:45 2019

@author: JOANRR
"""

from ..resources import sourcemeter


class keysight33210A(sourcemeter):
    """This class uses the sourcemeter class to open a resource instance froa fucntion generator from type 33500B from Keysight / Agilent Technologies"""
    
    def __init__(self, resource, unit = 'VPP'):
        sourcemeter.__init__(self,resource)
        if (self.identify[0:20] == "Agilent Technologies"):
            print('You have connected succesfully with a %s' % self.identify)
        else:
            raise  Exception('Not an Agilent Technologies family instrument, an instrument of type %s is detected' % self.identify)
        self.functions = ['SIN','SQU', 'RAMP', 'PULS', 'NOIS','DC','USER']
        
        self.units = ['VPP', 'VRMS', 'DBM']
        if unit not in self.units:
            raise ValueError(f'Unit {unit} no accepted. The options are:\n\t{self.units}')
        else:
            self.unit = unit
            self.inst.write("VOLT:UNIT {}".format(self.unit))  
        
        self.min_freq = 1e-3
        self.max_freq = 10e6
        self.load = 50
        self.Vmax = 5
        
    def set_load(self, load = 50, debug = False):
        """Sets the Load of the output it accepts 50 or HIGHz"""
        options = [50, 'INF']

        if load in options:
            self.load = load
            
            print(f'Setting the load to {load}') if debug else None
            if isinstance(load, (int, float)):
                string = f":OUTP:LOAD {load:.0f}"
                self.Vmax = 5
            else:
                self.Vmax = 10
                string = f":OUTP:LOAD {load}"
            self.inst.write(string)
            # print(f'Setting the load to {load}\n\t{string}')

        else:
            raise ValueError(f"Load option '{load}' not accepted")
    
    def apply(self, function, freq, amplitude, offset):
        """ You can select the function, frequency, amplitude, and offset all in one command. """
        if function not in self.functions:
            raise ValueError(f'Function {function} not available. Those are the available options:\n{self.functions}')
        
        
        string = f":APPL:{function} {freq:.4e}, {amplitude:.4f}, {offset:.4f}"
        # print(f'Configuring for: \n\t{string}')
        self.inst.write(string)
        
    def set_function(self, function,  debug = False):
        """Sets the output waveform function."""
        if function not in self.functions:
            raise ValueError(f"Function '{function}' not available. Options are:\n\t{self.functions}")
        
        func = self.inst.query("FUNC?").strip().upper()
        
        if func == function:
            print(f'Instrument already configured for {function}') if debug else None
        else:
            string = f"FUNC {function}"
            self.inst.write(string)
            print(f'Setting output function to {function}') if debug else None 
        
    def set_frequency(self, frequency, debug = False):
        """Sets the output frequency."""
        if isinstance(frequency, str):
            if frequency in ['MIN', 'MAX']:
                string = f"FREQ {frequency}"
            else:
                raise ValueError("Frequency string must be 'MIN' or 'MAX'")
        else:
            if self.min_freq <= frequency <= self.max_freq:
                string = f"FREQ {frequency:.4e}"
            else:
                raise ValueError('Frequency out of range!')
        self.inst.write(string)
        print(f'Setting frequency to {frequency:.46} Hz') if debug else None
        
    def set_amplitude(self, amplitude, debug = False):
        """Sets the output amplitude in the selected voltage unit."""
        if amplitude <= 0:
            raise ValueError('Amplitude must be positive!')
        string = f"VOLT {amplitude:.4f}"
        self.inst.write(string)
        print(f'Setting amplitude to {self.unit} = {amplitude:.4f} V') if debug else None
    
    def check_load(self,  debug = False):
        """Checks the output termination and returns (load, Vmax).
        Vmax = 5 V for 50 Ω, 10 V for high impedance (INF/HIGHZ).
        """
        load_str = self.inst.query(":OUTP:LOAD?").strip().upper()
        
        if load_str in ["INF", "HIGHZ", "HZ"]:
            Vmax = 10.0
            load = 'INF'
        else:
            try:
                load = float(load_str)
                # Treat values close to 50 as 50 Ω load
                Vmax = 5.0 if abs(load - 50) < 1e-3 else 10.0
            except ValueError:
                load = None
                Vmax = 5.0  # default fallback

        print(f"Detected load = {load} → Vmax = {Vmax:.1f} V") if debug else None
        self.load, self.Vmax = load, Vmax
        return load, Vmax
    
    def set_offset(self, offset,  debug = False):
        """Sets the DC offset in volts. It needs to fulfill |Voffset| < Vmax - Vpp/2"""
        # Get current amplitude in Vpp, Update load and Vmax, just in case
        load, Vmax = self.check_load()
        
        amp_str = self.inst.query("VOLT?").strip()
        try:
            amplitude = float(amp_str)
        except ValueError:
            amplitude = 0.0

        # Check the safety condition |Voffset| <= Vmax - Vpp/2
        if abs(offset) > (self.Vmax - amplitude / 2):
            raise ValueError(
                f"Offset {offset:.3f} V exceeds safe limits for current amplitude.\n"
                f"Condition: |Voff| ≤ Vmax – Vpp/2 = {self.Vmax - amplitude/2:.3f} V"
            )

        # Apply safely
        self.inst.write(f"VOLT:OFFS {offset:.4f}V")
        print(f'Setting offset to {offset:.4f} V (limit OK)') if debug else None

        
    def set_duty_cycle(self, duty, debug = False):
        """Sets the duty cycle for square waves (20%–80%)."""
        if not (20 <= duty <= 80):
            raise ValueError('Duty cycle must be between 20% and 80%.')
        # Check if function is square wave
        func = self.inst.query("FUNC?").strip().upper()
        if func != 'SQU':
            raise ValueError('Duty cycle can only be set for square wave (SQU) function.')
        
        string = f"FUNC:SQU:DCYC {duty:.0f}"
        self.inst.write(string)
        print(f'Setting duty cycle to {duty:.0f} %') if debug else None
    
    def set_dc_voltage(self, voltage, debug = False):
        """Sets a DC output voltage (uses the DC function)."""
        # Voltage range can typically be -5 V to +5 V (for 50 Ω load),
        # but you can adapt based on your instrument setup.
        if not (-self.Vmax <= voltage <= self.Vmax):
            raise ValueError(f'DC voltage must be between -{self.Vmax:.0f} V and +{self.Vmax:.0f} V.')

        # Select DC mode and set offset voltage
        self.inst.write("FUNC DC")
        self.inst.write(f"VOLT:OFFS {voltage:.4f}V")
        print(f'Setting DC output to {voltage:.4f} V') if debug else None

    def outpoff(self):
        """Turns off the instrument."""
        self.inst.write(":OUTP OFF")
    def outpon(self):
        """Turns on the instrument."""
        self.inst.write(":OUTP ON")
    
    def close(self):
        """Closes the resource instance."""
        self.inst.close()
    
    