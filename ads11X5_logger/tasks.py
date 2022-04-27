#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 14 10:14:38 2022

@author: pi
"""

import time
import os
import warnings

if os.name == 'nt':
    warnings.warn('Windows system, the modules for the adafruit will not be imported. ADS11X5_logger cannot be used.')

else:
    import board
    import busio
    from adafruit_ads1x15.analog_in import AnalogIn
    
from threading import Lock
from pathlib import Path
from pyInstruments import __file__ as module_folder

tempfile = Path(module_folder).parent / Path('temp/temp.dat')

class ADS11x5Logger():
    def __init__(self, channels_config = [('diff', (0,1))], gain =  1, address = 72, model = '1015'):
        
        # Files to store and read the setpoint and Treal
        self.log_file = tempfile
        self.gain = gain
        
        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        if model == '1015':
            import adafruit_ads1x15.ads1015 as ADS
            self.ads = ADS.ADS1015(i2c,gain = gain)
        elif model == '1115':
            import adafruit_ads1x15.ads1115 as ADS
            self.ads = ADS.ADS1115(i2c,gain = gain)
        else:
            raise ValueError(f'{model} is not an valid model, only "1115" or "1x15" accepted.')
            
        ## Channels internal names
        self._channels = [ADS.P0, ADS.P1, ADS.P2, ADS.P3]
        # Configure the channels
        self.configure_channels(channels_config = channels_config)
        
        # Creates a lock class to block the access to the temperature writing
        self.lock = Lock()
        # Files to store and read the setpoint and Treal
        self.log_file = tempfile
        self.internal_delay = 0.001 # Delay qhen adquiring voltage values between channels in s
        self.values = [None] * len(self.channels)
        
    def configure_channels(self, channels_config = [('diff', (0,1))]):
        
        self.channels = []
        
        for c in channels_config:
            if c[0] == 'diff':
                self.channels.append(AnalogIn(self.ads, *[self._channels[i] for i in c[1]]))
            elif c[0] == 'single':
                self.channels.append(AnalogIn(self.ads, c[1]))
            else:
                raise ValueError(f'Channel configuration not valid. Only "diff" and "single" accepted ({c[0]} not accepted.')
        
        return None    
    
    def measure(self, delay = 0.01, continuous = False, show_print = False, write_to_file = False, channel2export = 0):
        self.running = True
        self.delay = delay
        if show_print:
            print(("{:^8s}\t" * len(self.channels)).format(*[f'ch{i:d}' for i in range(len(self.channels))]))

        while self.running:
            try:
                for i, c in enumerate(self.channels):
                    self.values[i] = c.voltage
                    time.sleep(self.internal_delay)
#                self.values = [c.voltage for c in self.channels]
                
                if show_print:
                    print(('\r ' + "{:^8.5f}\t" * len(self.channels)).format(*self.values), end =''  )
                
                if write_to_file:
                    with self.lock:
                        temp = self.values[channel2export]
                        with open(self.log_file, 'w') as f:
                            f.write(f'{temp:8.6f}')
                
                time.sleep(self.delay)
                
                if not continuous:
                    break
            except OSError as e:
                print(e)
                if  e.args[0] == 121:
                    print('Check the connection of the ADC board!')
                else:
                    print('Something wrong with the ADC board...!')
                self.running = False 
                break
                
            except KeyboardInterrupt:
                print('\nMeasurement stopped.')
                self.running = False
                break

    def measurement_on(self):
        self.running = True
      
    def measurement_off(self):
        self.running = False