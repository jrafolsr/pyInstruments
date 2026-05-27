# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 10:42:52 2022

@author: JOANRR
"""
from pyInstruments import list_resources
from pyInstruments.instruments import keithley24XX
from time import sleep, monotonic
from datetime import datetime
from pathlib import Path
import numpy as np
from threading import Thread, Event
import queue
from pyInstruments import __file__ as module_folder
from pyInstruments import Timer
from scipy.stats import linregress


#%%

def dt_calc(etime):
    """Returns an interval of time that increased as the ellapsed time etime increases"""
    if etime <= 5:
        return 0.01
    elif etime <= 10:
        return 0.25
    elif etime <= 60:
        return 0.5
    elif etime <= 120:
        return 1.0
    elif etime <= 300:
        return 5.0
    elif etime <= 3600:
        return 10.0
    else:
        return 60.0

# New class

class SweepMyLEC():
    def __init__(self, resource, resource_pd, output_folder = 'sweep-my-lec'):
        
        self.device = keithley24XX(resource)
        
        self.photodiode = keithley24XX(resource_pd)
        
        self.set_output_folder(output_folder)
        
        self.bias_setpoint = np.nan
        
        
        self.time0 = monotonic()

        # Initialize array to save the last N points
        self.time_arr = np.zeros((2000, ))*np.nan
        self.voltage_arr = np.zeros((2000, ))*np.nan
        self.current_arr = np.zeros((2000, ))*np.nan
        self.photocurrent_arr = np.zeros((2000, ))*np.nan
        
        # Measuring loop interval
        self.dt_loop = 0.05# in seconds
        # Set the timer object
        self.main_timer = Timer(min_time_step=0.1, max_time_step=30, fix_step=False)
#        self.main_timer.initialize()
        # Timer to restart in enery change of current/voltage
        self.sub_timer = Timer(min_time_step=0.01, max_time_step=30, fix_step=False)
        
        # Solution for cleaninly updating the bias
        self._bias_update_queue = queue.Queue()
        
        # FTo run in CC or CV
        self.mode = None
        
    def pd_config(self, reverse_bias =  -5.0, **kwargs):
        self.photodiode.mode_vfix_configure(**kwargs)
        self.photodiode.mode_vfix_setvolt(reverse_bias)
    
    
    def pd_read(self):
        return self.photodiode.read()[1]
    
    def pd_outpon(self):
        self.photodiode.outpon()
    
    def pd_outpoff(self):
        self.photodiode.outpoff()
        
    def pd_reset_instrument(self):
        self.photodiode.reset()
        
        
    def set_output_folder(self, output_folder):
        self.output_folder = Path(output_folder)
        
        if not self.output_folder.exists():
            self.output_folder.mkdir()
        
    def reset_instrument(self):
        self.device.reset()
    
    def outpon(self):
        self.device.outpon()
    
    def outpoff(self):
        self.device.outpoff()
        
    def configure_V(self, voltage,**kwargs):
        self.mode = 'CV'
        self.device.mode_vfix_configure(**kwargs)
        self.set_voltage(voltage)
        
    def configure_I(self, current,**kwargs):
        self.mode = 'CC'
        self.device.mode_ifix_configure(**kwargs)
        self.set_current(current)

    def set_voltage(self, voltage):
        self.device.mode_vfix_setvolt(voltage)
        self.bias_setpoint = voltage
        

    def set_current(self, current):
        self.device.mode_ifix_setcurr(current)
        self.bias_setpoint = current
        
        
    def set_bias(self, value):
        if self.mode == 'CV':
            self.set_voltage(value)
        elif self.mode == 'CC':
            self.set_current(value)
        else:
            raise ValueError(f'Running mode {self.mode} not known. It must be either CV or CC')

    def request_bias_update(self, value):
        """Safely updating the bias """
        self._bias_update_queue.put(value)
        
        
    def configure_sweep(self, mode = 'list', sweep_list = [0, 1], nplc = 1, delay = 0.0, reset = True, ranging = 'auto'):
        self.device.configure_syncsweep_master(0, 1, step  = 0.1,\
                                         mode = mode, sweep_list=sweep_list,\
                                         nplc = nplc, delay = delay, reset=reset,\
                                         stay_on = True, ranging = ranging)
    
    def pd_configure_sweep(self, bias_voltage = -5.0, **kwargs):
#        print(kwargs)
        self.photodiode.configure_syncsweep_slave(bias_voltage, **kwargs)
    
    
    def read_V(self):
        return self.device.read()
    
    def run_sweep(self, delay = None, fileid = ''):
                
        timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss")
        etime = monotonic() - self.time0
        self.photodiode.init()
        self.device.init()
        self.sweep_data = self.device.fetch(delay)
        self.photocurrent = self.photodiode.fetch(delay = 0.0)
        
        self.sweep_data = self.sweep_data.reshape((self.sweep_data.shape[0] // 5, 5))
        self.photocurrent = self.photocurrent.reshape((self.photocurrent.shape[0] // 5, 5))[:,1]
        
        header = f'Ellapsed_time\t{etime:.2f}s\n'
        header += 'Voltage(V)\tCurrent(A)\tPhotocurrent\tInternal_time(s)'
        
        data2save = np.hstack((self.sweep_data[:,[0,1]], self.photocurrent.reshape(len(self.photocurrent), 1), self.sweep_data[:,[3]]))
        filename_suffix =  f'_Vsp={self.bias_setpoint:.2f}V_sweep_{fileid}.dat' if self.mode == 'CV' else f'_Isp={self.bias_setpoint:08.2e}A_sweep_{fileid}.dat'
        np.savetxt(self.output_folder / (timestamp +filename_suffix), data2save,\
                   fmt = '% 10.6e', header=header)
        Dt = self.sweep_data[-1, 3] - self.sweep_data[0, 3]
        print(f'\nSweep total time = {Dt:.4f} s')
            
        return self.sweep_data
    
    def stop_logger(self):
        self.running = False
        self.thread.join()
    
    def run_logger(self, filename = 'logger.dat', save_temperature = True):
        self.running = True
        
        output = self.output_folder / filename
        
        if not output.exists():
            with open(output,'a') as f:
                f.write(('#' +6*'{:^12}\t' + '\n').format('Time(s)','Voltage(V)','Current(A)', 'Internal time(s)', 'Photocurrent(A)','Temperature(C)'))
        
#        self.loop_time0 = monotonic()
        if not self.main_timer.initialized:
                    self.main_timer.initialize()
        
        self.sub_timer.initialize()
        
        self.device.outpon() if not self.device.outpstate() else None
        self.photodiode.outpon() if not self.photodiode.outpstate() else None
        
        
#        old_setpoint = self.bias_setpoint
        
        while self.running:
            try:
                if not self._bias_update_queue.empty():
                    new_setpoint = self._bias_update_queue.get_nowait() # Gets a value from the qeue without bloacking.
                    self.bias_setpoint = new_setpoint
                    self.set_bias(new_setpoint)
                    self.sub_timer.initialize()
                    self.time_arr *= np.nan
                    self.voltage_arr *= np.nan
                    self.current_arr *= np.nan  
                    self.photocurrent_arr *= np.nan
                    sleep(0.005)
                    
#                if not np.isclose(old_setpoint, self.bias_setpoint):
#                    unit = 'V' if self.mode == 'CV' else 'A'
#                    print(f'\nINFO: Updating bias from {old_setpoint:.2g} {unit} to {self.bias_setpoint:.2g} {unit}')
#                    self.set_bias(self.bias_setpoint)
#                    old_setpoint = self.bias_setpoint
#                    # Reset the loop_etime if we have changed Voltage!
#                    self.sub_timer.initialize()
#                    self.time_arr *= np.nan
#                    self.voltage_arr *= np.nan
#                    self.current_arr *= np.nan  
#                    self.photocurrent_arr *= np.nan
#                    
#                    sleep(0.005)
                     
                [voltage, current, _ , internal_time, _ ] =   self.device.read()
                
                
                # Quick control
                if self.mode =='CV':
                    if not np.isclose(voltage, self.bias_setpoint, 1e-5):
                        print(f'\nThe bias was not change ({voltage:.4f} V vs Vsp = {self.bias_setpoint:.2f}), atempting again to change it')
#                        old_setpoint = voltage
#                        continue
                
                time = self.main_timer.ellapsed_time()
                
                photocurrent = self.pd_read()

                self.time_arr[:-1] = self.time_arr[1:] 
                self.voltage_arr[:-1] = self.voltage_arr[1:] 
                self.current_arr[:-1] =self.current_arr[1:] 
                self.photocurrent_arr[:-1] =self.photocurrent_arr[1:] 
                self.time_arr[-1] = internal_time
                self.voltage_arr[-1] = voltage
                self.current_arr[-1] = current
                self.photocurrent_arr[-1] = photocurrent
                
                
                
                if self.sub_timer.istime2measure():
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
                            
                    with open(output,'a') as f:
                        f.write(('{:^10.6f}\t{:^10.6f}\t{:^10.6e}\t{:^10.6f}\t{:^10.6e}\t{:^ .2f}\n').format(time, voltage, current ,internal_time, photocurrent,temperature))
                
         
   
            except KeyboardInterrupt:
                # In case of error turn off the source anyway and stop the program
                print('INFO: Program interrupted in a safe way\n')
                self.stop_logger()
                
                break
            
            except Exception as e:
                # In case of ANY error turn off the source anyway and stop the program while printing the error
                print(e)
                self.stop_logger()
                break

#        self.device.outpoff() 
#        self.photodiode.outpoff()
                
    def run_logger_thread(self, filename = 'logger.dat'):
        self.thread = Thread(target = self.run_logger,kwargs = dict(filename = filename))
        self.thread.daemon = True
        self.thread.start()
        return None
    
    def sweep_and_log(self, sweep_list, logger_setpoint,\
                          logger_filename, logger_nplc = 1, logger_aver = True, logger_Ncount = 10,\
                          sweep_mode = 'list', sweep_nplc = 1, sweep_pd_nplc = 1, sweep_delay = 0.0, sweep_reset = True,
                          sweep_fileid = '', sweep_ranging = 'AUTO', sweep_pd_range = 'AUTO'):
        
        self.stop_logger()
        self.thread.join()
        
        print('INFO: The stopping the logger... Press Ctrl+C if it gets stuck here.')
        while self.thread.is_alive():
            try:
                sleep(0.01)
            except KeyboardInterrupt:
                break
        print('INFO: Logger stopped, performing sweep.')
        sleep(0.1)
            
        self.configure_sweep(mode = sweep_mode, sweep_list = sweep_list, nplc = sweep_nplc, delay = sweep_delay, reset = sweep_reset, ranging = sweep_ranging)
        
        self.pd_configure_sweep(nplc = sweep_pd_nplc, reset = sweep_reset, Npoints = len(sweep_list), ranging = sweep_pd_range)

        sleep(0.5)
        self.device.outpon() if not self.device.outpstate() else None
        self.run_sweep(fileid = sweep_fileid)
        
        # At the moment, I reset after the sweep, to clear all the triggers and shit
        logger_reset = False
        if self.mode == 'CV':
            self.configure_V(logger_setpoint, nplc = logger_nplc, aver = logger_aver, Ncount = logger_Ncount, reset = logger_reset)
        elif self.mode == 'CC':
            self.configure_I(logger_setpoint, nplc = logger_nplc, aver = logger_aver, Ncount = logger_Ncount, reset = True)
            
        self.pd_config(nplc = logger_nplc, aver = logger_aver, Ncount = logger_Ncount, reset = logger_reset, cmpl = 100e-6)
        
        print('INFO: Starting logger again...')
        
        self.run_logger_thread(logger_filename)
        
        return True



    def check_rate_condition(self, rate_condition, check_last_n_seconds = 30, verbose = True):
        ff = self.time_arr >= self.time_arr[-1] -  check_last_n_seconds #  Take only the last x seconds for the slope calculation
        # Dealing with the nan
        valid = ff & ~ np.isnan(self.time_arr) & ~np.isnan(self.current_arr)
        
        if np.count_nonzero(valid) > 10:
            # With more than N points I can already start doing a regression
            if self.mode == 'CC':
                slope, n, r, _, _ = linregress(self.time_arr[valid],self.voltage_arr[valid])           
                rate = slope * 1000* 60 #  Convert the rate into mV/min
                condition = np.abs(rate) <= rate_condition
                if verbose:
                    print(f'\r{self.main_timer.ellapsed_time(): 6.2f} s  {self.voltage_arr[-1]: 6.2f} V {self.current_arr[-1]*1000: 8.4f} mA  {rate: 6.2e} mV/min (target = {rate_condition: 6.2e} mV/min)', end = '\r')  

            elif self.mode == 'CV':   
                slope, n, r, _, _ = linregress(self.time_arr[valid],self.current_arr[valid])                
                # implementing rel. rate of change ad rrc = dj/dt/j
                rate = slope / self.current_arr[valid].mean()
                condition = np.abs(rate) <= rate_condition
                if verbose:
                    print(f'\r{self.main_timer.ellapsed_time(): 6.2f} s  {self.voltage_arr[-1]: 6.2f} V {self.current_arr[-1]*1000: 8.4f} mA  {rate: 6.2e} 1/s (target  = {rate_condition: 6.2e} 1/s)', end = '\r')   

        else:
            condition, rate = False, np.nan
        
        return condition, rate

# Old class, before 2024
#class SweepMyLEC():
#    def __init__(self, resource, resource_pd, output_folder = 'sweep-my-lec'):
#        
#        self.device = keithley24XX(resource)
#        
#        self.photodiode = keithley24XX(resource_pd)
#        
#        self.set_output_folder(output_folder)
#        
#        self.voltage_setpoint = np.nan
#        
#        self.time0 = monotonic()
#
#        
#    def pd_config(self, reverse_bias =  -5.0, **kwargs):
#        self.photodiode.mode_vfix_configure(**kwargs)
#        self.photodiode.mode_vfix_setvolt(reverse_bias)
#    
#    
#    def pd_read(self):
#        return self.photodiode.read()[1]
#    
#    def pd_outpon(self):
#        self.photodiode.outpon()
#    
#    def pd_outpoff(self):
#        self.photodiode.outpoff()
#        
#    def pd_reset_instrument(self):
#        self.photodiode.reset()
#        
#        
#    def set_output_folder(self, output_folder):
#        self.output_folder = Path(output_folder)
#        
#        if not self.output_folder.exists():
#            self.output_folder.mkdir()
#        
#    def reset_instrument(self):
#        self.device.reset()
#    
#    def outpon(self):
#        self.device.outpon()
#    
#    def outpoff(self):
#        self.device.outpoff()
#        
#    def configure_V(self, voltage,**kwargs):
#        self.device.mode_vfix_configure(**kwargs)
#        self.set_voltage(voltage)
#
#    def set_voltage(self, voltage):
#        self.voltage_setpoint = voltage
#        self.device.mode_vfix_setvolt(voltage)
#
#    def configure_sweep(self, mode = 'list', sweep_list = [0, 1], nplc = 1, delay = 0.0, reset = True, ranging = 'auto'):
#        self.device.configure_syncsweep_master(0, 1, step  = 0.1,\
#                                         mode = mode, sweep_list=sweep_list,\
#                                         nplc = nplc, delay = delay, reset=reset,\
#                                         stay_on = True, ranging = ranging)
#    
#    def pd_configure_sweep(self, bias_voltage = -5.0, **kwargs):
##        print(kwargs)
#        self.photodiode.configure_syncsweep_slave(bias_voltage, **kwargs)
#    
#    
#    def read_V(self):
#        return self.device.read()
#    
#    def run_sweep(self, delay = None, fileid = ''):
#                
#        timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss")
#        etime = monotonic() - self.time0
#        self.photodiode.init()
#        self.device.init()
#        self.sweep_data = self.device.fetch(delay)
#        self.photocurrent = self.photodiode.fetch(delay = 0.0)
#        
#        self.sweep_data = self.sweep_data.reshape((self.sweep_data.shape[0] // 5, 5))
#        self.photocurrent = self.photocurrent.reshape((self.photocurrent.shape[0] // 5, 5))[:,1]
#        
#        header = f'Ellapsed_time\t{etime:.2f}s\n'
#        header += 'Voltage(V)\tCurrent(A)\tPhotocurrent\tInternal_time(s)'
#        
#        data2save = np.hstack((self.sweep_data[:,[0,1]], self.photocurrent.reshape(len(self.photocurrent), 1), self.sweep_data[:,[3]]))
#        
#        np.savetxt(self.output_folder / (timestamp + f'_Vsp={self.voltage_setpoint:.2f}V_sweep_{fileid}.dat'), data2save,\
#                   fmt = '% 10.6e', header=header)
#        Dt = self.sweep_data[-1, 3] - self.sweep_data[0, 3]
#        print(f'\nSweep total time = {Dt:.4f} s')
#            
#        return self.sweep_data
#    
#    def stop_logger(self):
#        self.running = False
#        self.thread.join()
#    
#    def run_logger(self, filename = 'logger.dat', save_temperature = True):
#        self.running = True
#        
#        output = self.output_folder / filename
#        
#        if not output.exists():
#            with open(output,'a') as f:
#                f.write(('#' +6*'{:^12}\t' + '\n').format('Time(s)','Voltage(V)','Current(A)', 'Internal time(s)', 'Photocurrent(A)','Temperature(C)'))
#        
#        self.loop_time0 = monotonic()
#        
#        self.device.outpon() if not self.device.outpstate() else None
#        self.photodiode.outpon() if not self.photodiode.outpstate() else None
#            
#        old_setpoint = self.voltage_setpoint
#        
#        while self.running:
#            try:
#                if old_setpoint != self.voltage_setpoint:
#                    print(f'\nINFO: Updating voltage from {old_setpoint:.2f} V to {self.voltage_setpoint:.2f} A')
#                    self.set_voltage(self.voltage_setpoint)
#                    old_setpoint = self.voltage_setpoint
#                    # Reset the loop_etime if we have changed Voltage!
#                    self.loop_time0 = monotonic()                    
#                    sleep(0.005)
#                    
#                loop_time = monotonic() # Time of the WHILE loop
#                total_etime = loop_time - self.time0 # Total ellapsed time since we start the object
#                logger_etime = loop_time - self.loop_time0 # Ellapsed time since the call to the logger, to reset the time adqusition after each call
#                     
#                [voltage, current, _ , internal_time, _ ] =   self.device.read()
#                photocurrent = self.pd_read()
#
#                                   
#                if save_temperature:
#                    with open(Path(module_folder).parent / 'temp/temp.dat') as f:
#                        try:
#                            temperature = float(f.read())
#                        except ValueError:
#                            temperature = np.nan
#                else:
#                    temperature = np.nan
#                    
#                with open(output,'a') as f:
#                    f.write(('{:^10.6f}\t{:^10.6f}\t{:^10.6e}\t{:^10.6f}\t{:^10.6e}\t{:^ .2f}\n').format(total_etime, voltage, current ,internal_time, photocurrent,temperature))
#                
#                sleeping_time = dt_calc(logger_etime)
#                
#                print(f'\r{total_etime: 6.2f} s\t{voltage: 6.2f} V\t{current*1000: 8.4f} mA\t{photocurrent*1e6: 6.4f} uA', end = '\r')        
#                
#                while (monotonic() - loop_time) < sleeping_time and self.running:
#                    sleep(0.01)
#   
#            except KeyboardInterrupt:
#                # In case of error turn off the source anyway and stop the program
#                print('INFO: Program interrupted in a safe way\n')
#                self.stop_logger()
#                
#                break
#            
#            except Exception as e:
#                # In case of ANY error turn off the source anyway and stop the program while printing the error
#                print(e)
#                self.stop_logger()
#                break
#
##        self.device.outpoff() 
##        self.photodiode.outpoff()
#                
#    def run_logger_thread(self, filename = 'logger.dat'):
#        self.thread = Thread(target = self.run_logger,kwargs = dict(filename = filename))
#        self.thread.daemon = True
#        self.thread.start()
#        return None
#    
#    def sweep_and_log(self, sweep_list, logger_voltage,\
#                          logger_filename, logger_nplc = 1, logger_aver = True, logger_Ncount = 10,\
#                          sweep_mode = 'list', sweep_nplc = 1, sweep_pd_nplc = 1, sweep_delay = 0.0, sweep_reset = True,
#                          sweep_fileid = '', sweep_ranging = 'AUTO', sweep_pd_range = 'AUTO'):
#        
#        self.stop_logger()
#        self.thread.join()
#        
#        print('INFO: The stopping the logger... Press Ctrl+C if it gets stuck here.')
#        while self.thread.is_alive():
#            try:
#                sleep(0.01)
#            except KeyboardInterrupt:
#                break
#        print('INFO: Logger stopped, performing sweep.')
#        sleep(0.1)
#            
#        self.configure_sweep(mode = sweep_mode, sweep_list = sweep_list, nplc = sweep_nplc, delay = sweep_delay, reset = sweep_reset, ranging = sweep_ranging)
#        
#        self.pd_configure_sweep(nplc = sweep_pd_nplc, reset = sweep_reset, Npoints = len(sweep_list), ranging = sweep_pd_range)
#
#        sleep(0.5)
#        self.run_sweep(fileid = sweep_fileid)
#        
#        # At the moment, I reset after the sweep, to clear all the triggers and shit
#        logger_reset = False
#        self.configure_V(logger_voltage, nplc = logger_nplc, aver = logger_aver, Ncount = logger_Ncount, reset = logger_reset)
#        self.pd_config(nplc = logger_nplc, aver = logger_aver, Ncount = logger_Ncount, reset = logger_reset, cmpl = 100e-6)
#        
#        print('INFO: Starting logger again...')
#        
#        self.run_logger_thread(logger_filename)
#        
#        return True
#%%        
        
if __name__ == '__main__':
    
    folder = Path('testing-IVL-sweep')
    if not folder.exists(): folder.mkdir()
    
    m = SweepMyLEC('GPIB0::25::INSTR', 'GPIB0::26::INSTR', output_folder = folder)
    
    m.pd_config(-6.0, nplc = 1, Ncount = 10)
    
    m.pd_outpon()

