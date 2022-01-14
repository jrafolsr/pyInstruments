#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 14 10:14:38 2022

@author: pi
"""

import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from threading import Lock
from pathlib import Path
from pyInstruments import __file__ as module_folder

tempfile = Path(module_folder).parent / Path('temp/temp.dat')

class ADS11x5Logger():
    def __init__(self, channels_config = [('diff', (0,1))], gain =  1):
        
        # Files to store and read the setpoint and Treal
        self.log_file = tempfile
        self.gain = gain
        
        # Create the I2C bus
        i2c = busio.I2C(board.SCL, board.SDA)

        # Create the ADC object using the I2C bus
        self.ads = ADS.ADS1115(i2c,gain = gain)
        ## Channels internal names
        self._channels = [ADS.P0, ADS.P1, ADS.P2, ADS.P3]
        # Configure the channels
        self.configure_channels(channels_config, gain)
        
        # Creates a lock class to block the access to the temperature writing
        self.lock = Lock()
        # Files to store and read the setpoint and Treal
        self.log_file = tempfile
        
        self.values = [None] * len(self.channels)
        
    def configure_channels(self, channels_config = [('diff', (0,1))], gain = 1):
        self.gain = gain
        
        self.channels = []
        
        for c in channels_config:
            if c[0] == 'diff':
                self.channels.append(AnalogIn(self.ads, *[self._channels[i] for i in c[1]]))
            elif c[0] == 'single':
                self.channels.append(AnalogIn(self.ads, c[1]))
            else:
                raise ValueError('Channel configuration not valid. Only "diff" and "single" accepted.')
        
        return None    
    def measure(self, delay = 0.5, continuous = False, channel2export = 0, show_print = False):
        self.running = True
        self.delay = delay
        if show_print:
            print(("{:^8s}\t" * len(self.channels)).format(*[f'ch{i:d}' for i in range(len(self.channels))]))

        while self.running:
            try:
                self.values = [c.voltage for c in self.channels]
                if show_print:
                    print(('\r ' + "{:^8.5f}\t" * len(self.channels)).format(*self.values), end =''  )
                
                with self.lock:
                    temp = self.values[channel2export]
                    with open(self.log_file, 'w') as f:
                        f.write(f'{temp:8.6f}')
                
                time.sleep(self.delay)
                
                if not continuous:
                    break
            except KeyboardInterrupt:
                print('\nMeasurement stopped.')
                break

    def measurement_on(self):
        self.running = True
      
    def measurement_off(self):
        self.running = False