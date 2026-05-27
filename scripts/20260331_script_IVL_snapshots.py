#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 20:45:22 2022

@author: JOANRR
"""
from pyInstruments.ivl_snapshots import SweepMyLEC
from time import sleep,monotonic
from datetime import datetime
from pathlib import Path
import numpy as np
import shutil


#%%
# Waiting time function, it is only an upper limit if the slope of the transient is used.
waiting_calc = lambda V: 2*3600 #(-7.5 * (V - 3) + 45) * 60  # 45 min for the low voltgae, 30 min for the high
# Set time after sweep
time_after_sweep =  180
min_time_per_current_step = 60 #waiting_calc(0) # Minimum time per current

# Set the folder and the file_id. The program will automaticallu create a subfolder with the file_id
folder = Path('/home/pi/Documents/data/Sri')
file_id = '22-SP02-04b'

mode = 'CV'             # The only one implemented, so far
rate_condition = 1e-5   # Rate in mV/min if CC or 1/s (dj/dt / j) if CV (to bE changed) at which to change current step

list_voltages = [2.75,3.00,3.25]# list(np.round(np.arange(2.75, 3.01, 0.25),2))

#%% Run a pre-bias protocol at CV or CC
run_prebias          = True
mode_prebias        = 'CC'
bias_prebias        = 0.4      # Current in mA or voltage in V
max_time_prebias    = 5.5*3600     # Max time allowed for the prebias
min_time_prebias    = 300      # Min time allowed for the prebias bfore the condition is met
condition_prebias   = 0.2     # mV/min or 1/s, always positiove, as I am only checking the abs rate, consider chaning it

bias_prebias = bias_prebias if mode_prebias == 'CV' else bias_prebias/1000
#%%

# Staircase options
N_staircase = 1 # Number of times repeating the staircase
staircase_downscan = True
if staircase_downscan:
    list_voltages = list_voltages + list_voltages[-2::-1]


# MAIN CODE, DO NOT TOUCH UNLESS YOU KNO WHAT ARE YOU DOING
folder = folder /file_id
if not folder.exists(): folder.mkdir()

logfile = folder / (file_id + '_intervals.log')
with open(logfile, 'w') as f:
            f.write('Total_time[s]\tEllapsed_time[s]\tVoltage[V]\tCurrent[A]\tPhotourrent[A]\trate[mV/min or 1/s]\tCondition_Status\tRun#\n')

#%%
# Sweep options: set fast I-V sweep voltages  
Vstart = 0
Vend = 5.0
step = 0.25
sweep_downscan = True # Whether or not to do the downscan for the sweeP
sweep_ranging = 'AUTO'
sweep_delay = 0.020 # Add a 10 ms delay
sweep_nplc = 1
sweep_pd_range = 'AUTO'
sweep_pd_nplc = sweep_nplc


# Control to ensure the proper I-V sweep, so we don't scan less than Vbias
if max(list_voltages) > Vend:
    print(f'The fast I-V sweep does not cover the max Vbias input {Vend} V vs Vbias = {max(list_voltages)}')
    flag_continue = bool(input('\tAbort and fix it -> 0\n\tContinue -> 1\n'))
    if not flag_continue:
        raise ValueError('Stopping the script')

# I add extra point in the gap, between 2 and 3 V
sweep_voltage = np.concatenate([np.arange(Vstart, 1.5, 0.3),np.arange(1.5, 2.50, 0.1), np.arange(2.50, Vend+ 0.01,step)])

if sweep_downscan:
     # Obs! remove 8 for nothing in case you want a full sweep back
    sweep_voltage = np.concatenate([sweep_voltage ,sweep_voltage[-2::-1]])
#%%
# Setting te resources (Keitheys) adn measurement condtions)
resource_led = 'GPIB0::25::INSTR'
resource_pd = 'GPIB0::26::INSTR'

pd_bias = -5.0 # Reverse bias for the voltage readout

m = SweepMyLEC(resource_led, resource_pd, output_folder = folder)    
#    m.reset_instrument()
kwargs_staircase = dict(reset = True, nplc = 1, aver = False, Ncount = 1, fw=False)

kwargs_pd = dict(kwargs_staircase)
kwargs_pd['cmpl'] = 100e-6
# Configure the photodiode-reading Keithley
m.pd_config(pd_bias, **kwargs_pd)
rate_condition_flag = False
try:
    # Add the pre bias step in case it i True
    if run_prebias:
        print(f'Running the prebias protocol at {mode_prebias}')
        if mode_prebias == 'CC':
            m.configure_I(bias_prebias, **kwargs_staircase)
        elif mode_prebias == 'CV':
            m.configure_V(bias_prebias, **kwargs_staircase)
        else:
            print(f'Mode "{mode}" no implemented, only "CV" or "CC"')
        
        timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss_")
        logger_filename = timestamp + file_id + f'_prebias{mode_prebias}.dat'
        m.run_logger_thread(logger_filename)
    
        while m.sub_timer.ellapsed_time() < max_time_prebias:
            condition, rate = m.check_rate_condition(condition_prebias)
            # Check if the condition and accept it only if min_time_per_current_step have passed (to avoid any spurious initial dVdt)

            if condition and not rate_condition_flag:
                print(f'\nINFO: Rate condition reached with {rate:.2e} 1/s at {m.sub_timer.ellapsed_time():.2f} s')
                rate_condition_flag = True              # Flag ackownledging that thr rate condition was met
            
            if rate_condition_flag and m.sub_timer.ellapsed_time() >= min_time_prebias:
                print(f'\nINFO: Rate condition & min_time_prebias condition reached with {rate:.2e} mV/min at {m.sub_timer.ellapsed_time():.2f} s')
                break
            
        m.stop_logger()
        m.thread.join()
        if not rate_condition_flag: 
            print(f'\nINFO: Steady state condition reached by time {max_time_prebias:.2f} s, with {rate:.2e} 1/s')
    
            
    print(f'Running the staircase protocol at {mode}')
    
    # Configure the staircase measurement
    # Configure the power-supplier Keithley
    m.configure_V(list_voltages[0], **kwargs_staircase)
    
    timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss_")
    logger_filename = timestamp + file_id + '_staircase_run1.dat'
    
    m.run_logger_thread(logger_filename)
    

    for k in range(1,N_staircase + 1):
        logger_filename = timestamp + file_id + f'_staircase_run{k}.dat'
        
        for i, voltage in enumerate(list_voltages):
#            m.bias_setpoint = voltage
            m.request_bias_update(voltage)
            sleep(0.2)
            
            sleeping_time = waiting_calc(voltage)
            print(f'\nGoing to sleep for {sleeping_time} sec')
            
            # Reset some flags
            rate_condition_flag = False
            
            while m.sub_timer.ellapsed_time() < sleeping_time: # OBS!rEMOVE THE TIME_AFTER SWEEP!

                condition, rate = m.check_rate_condition(rate_condition, check_last_n_seconds=30)

                # Check if the condition and accept it only if hard coded 30 s have passed (to avoid any spurious initial dVdt)
                if condition and not rate_condition_flag and m.sub_timer.ellapsed_time() >= 30:
                    print(f'\nINFO: Steady state rate condition reached with {rate:.2e} 1/s at {m.sub_timer.ellapsed_time():.2f} s')
                    rate_condition_flag = True              # Flag ackownledging that thr rate condition was met
                
                # Check if the condition and accept it only if min_time_per_current_step have passed (to avoid any spurious initial dVdt)
                if rate_condition_flag and m.sub_timer.ellapsed_time() >= min_time_per_current_step:
                    print(f'\nINFO: Steady state condition & min_time_per_current_step condition reached with {rate:.2e} 1/s at {m.sub_timer.ellapsed_time():.2f} s')
                    break
            
            if not rate_condition_flag: 
                print(f'\nINFO: Steady state condition reached by time {sleeping_time:.2f} s, with {rate:.2e} 1/s')
        
            with open(logfile, 'a') as f:
    #            f.write('Total_time[s]\tEllapsed_time[s]\tVoltage[V]\tCurrent[mA]dVdt[mV/min]\tCondition_Status\n')
                f.write('{:.2f}\t{:.2f}\t{:.4f}\t{:10.6e}\t{:10.6e}\t{:8.4e}\t{}\t{:02d}\n'.format(m.main_timer.ellapsed_time(),\
                                                                            m.sub_timer.ellapsed_time(),\
                                                                            m.voltage_arr[-1],\
                                                                            m.current_arr[-1],\
                                                                            m.photocurrent_arr[-1],\
                                                                            rate,\
                                                                            rate_condition_flag,
                                                                            k))    
                    
           
            print(f'\nPerforming sweep number #{i} of run #{k}')

            sweeper_filename = file_id + f'_run{k}'  
            
            m.sweep_and_log(np.append(sweep_voltage, voltage), voltage, logger_filename, logger_aver=False, logger_Ncount=1, logger_nplc=1, sweep_fileid = sweeper_filename, sweep_ranging = sweep_ranging, sweep_reset = False, sweep_delay = sweep_delay, sweep_nplc = sweep_nplc, sweep_pd_range = sweep_pd_range, sweep_pd_nplc = sweep_pd_nplc)
            

            time0 = monotonic()
            
            print(f'\nGoing to sleep for {time_after_sweep:.2f} s')
            
            while (monotonic() - time0) < time_after_sweep:
                sleep(0.1)
            
            # Reset some flags
#            rate_condition_flag = False
#            m.sub_timer.initialize()

    print('\nCheckpoint 1')
    m.bias_setpoint = list_voltages[0]
    
    sleep(0.05)
    print('\nCheckpoint 2')
    m.stop_logger()
    
    
except KeyboardInterrupt:
    print('\nINFO: Terminating program')  
except Exception as e:
    print(e)
    print('\nINFO: Terminating program')  
  

sleep(0.05)
#    m.outpoff()  
print('\nCheckpoint 4')
    
m.stop_logger()

m.outpoff()
m.pd_outpoff()
timestamp = datetime.now().strftime("%Y-%m-%d")
shutil.copy(__file__, folder / f'{timestamp}_measurement_script.py')

print('INFO: Program terminated.')
