#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 26 11:26:47 2022

@author: pi
"""

from pyInstruments.ads11X5_logger import ADS11x5Logger

from time import sleep

meas = ADS11x5Logger(channels_config = [('single',  3)], gain = 1, address = 72)

#meas2 = ADS11x5Logger(channels_config = [('single',  3)], gain = 1, address = 72)

while True:
    try:
        meas.measure()
#        meas2.measure()
        values = meas.values
        
#        meas2.measure()
        
#        values2 = meas2.values
        
#        print(f'\r Reading ADC74: {values[0]:5.4f} V, ADC72: {values2[0]:5.4f}', end = '\r')
        print(f'\r Reading: {values[0]:5.4f} V', end = '\r')
        
        sleep(0.1)
        
    except KeyboardInterrupt:
        break
    