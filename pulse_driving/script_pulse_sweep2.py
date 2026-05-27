# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 14:01:50 2025

@author: JOANRR
"""

import numpy as np
from time import sleep, monotonic
from pyInstruments.instruments import keysight33210A, keysight34461A, keithley24XX # This the module I created
from datetime import datetime
from collections import deque
from pathlib import Path
from pyInstruments import list_resources, Timer
from pyInstruments import __file__ as module_folder

resources = list_resources()

folder = Path(r'/home/pi/Documents/data/joan/2025_pulsed-lec')
fileid= 'H03D2-pushing'

path = folder / fileid
path.mkdir() if not path.exists() else None
save_temperature = False


duty_cycles = [100] +np.round(np.arange(75, 24, -25), 0).tolist()
duty_cycles.reverse()
duty_cycles = duty_cycles + duty_cycles[1::-1]
#duty_cycles = [100, 80, 40, 80, 100]
# Calculate the amplitude if I want to keep the Vavg fixed!
function = 'SQU'
frequency = 50
Vavg = 2.5
Vmax = 10
Vref = 0
time_per_duty = 1200

calc_Vpp = lambda d, Vavg, Vref: (Vavg-Vref) / (d/100)
calc_Vmax = lambda d, Vavg, Vref: calc_Vpp(d, Vavg, Vref) + Vref
#    
list_dcyc = [d for d in duty_cycles if calc_Vmax(d, Vavg, Vref) <= Vmax]
list_Vpp = [calc_Vpp(d, Vavg, Vref) for d in duty_cycles if calc_Vmax(d, Vavg, Vref) <= Vmax]
#%%
main_timer = Timer(min_time_step=time_per_duty, max_time_step=time_per_duty, fix_step=True)
meas_timer = Timer(min_time_step = 0.1, max_time_step=5, fix_step=False)

wg = keysight33210A('GPIB0::20::INSTR')
mult_voltage = keysight34461A('GPIB0::3::INSTR')
smu_pd =  keithley24XX('GPIB0::26::INSTR')
smu_lec = keithley24XX('GPIB0::25::INSTR')

mult_voltage.config_volt(rang = 10, nplc = 1, count = 5)
  
kwargs_current = dict(term = 'FRONT', fw = False, cmpl = 0.1, beeper = True, aver = True,\
                        Ncount = 5, nplc = 1)
pd_range = 10e-6
lec_range = 10e-3
smu_pd.mode_vfix_configure(**kwargs_current, sens_curr_ranging = pd_range)
smu_lec.mode_vfix_configure(**kwargs_current, sens_curr_ranging = lec_range)
#%%
smu_pd.outpon()
smu_lec.outpon()
#    
wg.outpoff()
# COnfiguring the waveform generator
wg.set_load('INF')
wg.set_function(function)
wg.set_frequency(frequency)
wg.set_amplitude(list_Vpp[0])
wg.set_duty_cycle(50)
#%%


try: 
    for frequency in [50, 100, 500, 1000]:
#        wg.set_frequency(frequency)
        timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss")
        filename = path / (timestamp + '_' + fileid + f'_{frequency:.1e}Hz.dat')
        
        if not filename.exists():
            with open(filename,'w') as f:
                f.write(('#' +9*'{:^12}\t' + '\n').format('Total_time(s)','Step_time(s)','Voltage_avg(V)', 'Device_current(A)', 'Photocurrent(A)','Duty_cycle(%)', 'V_pp(V)','V_offset(V)', 'Temperature(C)'))
    

        main_timer.initialize()
        for d, Vpp in zip(list_dcyc, list_Vpp):
            print(f'>>>>>>>Setting a duty cycle of {d:.0f} %  and  Vpp = {Vpp:.2f}<<<<<<<<')
    
            if np.isclose(d, 100):
                wg.set_dc_voltage(Vpp)
                wg.outpon()               
            else:
                # wg.outpon() if not flag_on else pass
                wg.outpoff()
                wg.set_load('INF')
                wg.set_frequency(frequency)
                wg.set_function(function)
                wg.set_duty_cycle(d)
                wg.set_amplitude(Vpp)
                wg.set_offset(Vpp/2)
                wg.outpon()
        
            meas_timer.initialize()    
    
            while True:
                

                
                t0 = main_timer.ellapsed_time()
                t0m = meas_timer.ellapsed_time()
                lec_voltage = mult_voltage.read().mean()
                [voltage, pd_current, _ , internal_time, _ ] =   smu_pd.read()
                [voltage, lec_current, _ , internal_time, _ ] =   smu_lec.read()
                t_total = (main_timer.ellapsed_time()-t0)/ 2 + t0
                t_step = (meas_timer.ellapsed_time()-t0m)/ 2 + t0m
                
                # Update ranges if needed:
                # The maximum value will correspnt to the  Iavg duty cycle divided by the 
                _value = np.log10(np.abs(pd_current/(d/100) * 1.5))
                
                # The bits need to be enabled!!! My peak currets are messing with my autorange
#                cond = int(smu_pd.inst.query(":STAT:OPER:COND?")) & 1024
                
                if (_value - np.log10(pd_range) > 0): 

                    pd_range=10**(min(np.log10(pd_range) +1, 0))
                    print(f'\nIncreasing the PD range to: {pd_range:.0e} A')
                    smu_pd.update_sensing_current_range(pd_range)
                
#                    print(smu_lec.inst.query(":SENS:CURR:RANG?"))
                elif  _value - np.log10(pd_range) < -1:
                    # Decrease range
                    pd_range = 10**(min(np.log10(pd_range) -1, -6))
                    
                    print(f'\nLowering the PD range to: {pd_range:.0e} A')
                    smu_pd.update_sensing_current_range(pd_range)

                
                _value = np.log10(np.abs(lec_current/(d/100) * 1.5))
                
                # 1024 is the overflow conditon, the range is too tight
#                cond = int(smu_lec.inst.query(":STAT:OPER:COND?")) & 1024
                if (_value - np.log10(lec_range) > 0):
                    # Increase range
                    lec_range=10**(min(np.log10(lec_range) +1, 0))
                    print(f'\nIncreasing the device range to: {lec_range:.0e} A')
                    smu_lec.update_sensing_current_range(lec_range)                   
                elif  _value - np.log10(lec_range) < -1:
                    # Decrease range
                    lec_range = 10**(min(np.log10(lec_range) -1, -6))
                    
                    print(f'\nLowering the device range to: {lec_range:.0e} A')
                    smu_lec.update_sensing_current_range(lec_range)
 
                
                print('\r{:.0f} s, {:^ .0f} %, {:6.4f} Vpp, {:6.4f} V, {:6.4f} mA, {:^10.4f} uA'.format(time_per_duty - t_step, d, Vpp, lec_voltage, lec_current*1000, pd_current*1e6), end='\r')
                
                if meas_timer.istime2measure():
                    if save_temperature:
                        with open(Path(module_folder).parent / 'temp/temp.dat', 'r') as f:
                            try:
                                string = f.read()
                                temperature = float(string)
                            except ValueError:
                                print(string)
                                temperature=np.nan
                    else:
                        temperature = np.nan
                    
                    with open(filename,'a') as f:
                        f.write(('{:^10.6f}\t{:^10.6f}\t{:^10.6f}\t{:^10.6e}\t{:^10.6e}\t{:^ .0f}\t{:^10.6f}\t{:^10.6f}\t{:^ .2f}\n').format(t_total, t_step, lec_voltage,lec_current, pd_current,d, Vpp, Vref+Vpp/2, temperature))
                
                if main_timer.istime2measure():
                    break
#        print()
    
    
    
except KeyboardInterrupt:
    pass
finally:
    
    wg.outpoff()
    sleep(4)
    smu_pd.outpoff()
    smu_lec.outpoff()