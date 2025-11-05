# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 14:01:50 2025

@author: JOANRR
"""

import numpy as np
from time import sleep, monotonic
from pyInstruments.instruments import keysight33210A # This the module I created
import datetime
from collections import deque
from pathlib import Path
from pyInstruments import list_resources

resources = list_resources()
resource = resources[0] if len(resources) else None
#%%
if not 'GPIB' in resource:
    raise ValueError('THe resource is not a GPIB one!')

print(f'Connecting to resource: {resource}')


try: 
    wg = keysight33210A(resource)
    
    wg.outpoff()
    
    
    duty_cycles = [100] +np.round(np.arange(80, 30, -10), 0).tolist()
    
    duty_cycles = [80, 40]*5
    # Calculate the amplitude if I want to keep the Vavg fixed!
    function = 'SQU'
    frequency = 50
    Vavg = 3
    Vmax = 10
    time_per_duty = 20
    
    
    calc_Vp  = lambda d, Vavg:  Vavg / (2  *(d/100)) 
    calc_Vpp  = lambda d, Vavg: 2* Vavg / (2  *(d/100))
    calc_Vmax = lambda d, Vavg: calc_Vpp(d, Vavg)
    
    list_dcyc = [d for d in duty_cycles if calc_Vmax(d, Vavg) <= Vmax]
    list_Vpp = [calc_Vpp(d, Vavg) for d in duty_cycles if calc_Vmax(d, Vavg) <= Vmax]
    
    # COnfiguring the waveform generator
    wg.set_load('INF')
    wg.set_function(function)
    wg.set_frequency(frequency)
    wg.set_amplitude(list_Vpp[0])
    wg.set_duty_cycle(50)

    # print(list_dcyc)
    # print(filtered_Vpp)
    
   
    flag_on = False
    for d, Vpp in zip(list_dcyc, list_Vpp):
        
        t0 = monotonic()
        print(f'>>>>>>>Setting a duty cycle of {d:.0f} %  and  Vpp = {Vpp:.2f}<<<<<<<<')
        
        if np.isclose(d, 100):
            wg.set_dc_voltage(Vpp)
            wg.outpon()
            flag_on = True
        else:
            # wg.outpon() if not flag_on else pass
            wg.outpoff()
            wg.set_function(function)
            wg.set_duty_cycle(d)
            wg.set_amplitude(Vpp)
            wg.set_offset(Vpp/2)
            wg.outpon()

            
        while (monotonic()-t0)<time_per_duty:
            print(f'\rSleeping for {time_per_duty - (monotonic()-t0):.0f} s', end='\r')
            sleep(0.01)
        print()
    
    
    
except Exception as e:
    print(e)
finally:
    wg.outpoff()