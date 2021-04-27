# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 10:37:57 2020

@author: OPEGLAB
"""


# coding: utf-8
# Library that depends on the pyLab library and that contains the main program/functions
# for driving the LEC devices at diferent modes.

import numpy as np
from time import sleep, time
from pyInstruments.instruments import keithley24XX # This the module I created
import datetime
import os
from os.path import join as pjoin
from pyInstruments.ivlogger import global_settings_iv as gs

ABSOLUTE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def dt_calc(etime):
    """Returns an interval of time that increased as the ellapsed time etime increases"""
    if etime <= 10:
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
 
        
def iv_setup(value, mode = 'CC', rtime = np.inf, dt = 0.25,\
                    folder = '.\\', fname = 'voltage-time-data',\
                    resource1 = 'GPIB0::24::INSTR', term = 'FRONT',\
                    fw = False, beeper = True, cmpl = 21.0,\
                    Ncount = 1, aver = False, nplc = 1.0,
                    config = True, interrupt_measurement = False,dt_fix = True):
    """Same as ivl_setup_v2 but with the photodiode adquisition made by a USB daq
    Mandatory arguments and using globals:
        - current: current in mA
    Optional arguments:
        - rtime: running time of the experiment in seconds, infinit by default
        - dt: time inverval between measueements.
        - folder: folder path where to save the file, abs o relative, current directory by default.
        - fname: filename where to save the data. Always append if the file already exists
        - resource1: resource name for the sourcemeter Keithley24XX, default is 'GPIB0::24::INSTR'
        - device: resource name for the DAQ device, 
        - term: either FRONT (default) or REAR for the sourmeter
        - config: if True (default) the sourcemeter from resource 1 is assumed that has to be configured, otherwise just reads the values
        - interrupt_measurement: if True, when the program is interrupted, the sourcemeter from resource 1 will stop only measuring, but will continue on ON state. Default is False (interrupts both measurement and sourcemeter)
        - Ncount: number of samples to ask the sourcemeter/multimeter, shared parameter. Default is 1
        - aver: Average the number of samples given for Ncount. Default is False- Shared parameter between  sourcemeter/multimeter.
        - nplc: Number of pulse ligh cycles to measure. Shared between sourcemeter/multimeter and default i 1.
        - fw: Activate the four-wire measurement (for the sourcemeter).
        - beeper: Activate the beeper (for the sourcemeter).
        - cmpl: compliance fot the sourcemeter (in volts since we are asking for current)
        - config: either to config (or not) the sourcemeter and multimeter, by default is True. If set False and it is really not configured, will  just complain and not work.
        - interrupt_measurement: dflt is False, if set to True when the program is interrupted, the measurement will stop but not the sourcemeter, that will continue feeding the device.
        - dt_fix: the time interval is fixed. If set to false, then it uses the time interval from the function dt_calc()
    """
    # Configuration only done if not done before
    ky2400 = keithley24XX(resource1)
    
    gs.SET_VALUE = value
    
    if gs.CONFIG_STATUS:
        if mode == 'CC':
            ky2400.mode_ifix_configure(fw = fw, beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount, nplc = nplc, aver = aver)
        elif mode == 'CV':
            ky2400.mode_vfix_configure(fw = fw, beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount, nplc = nplc, aver = aver)
        else:
            raise Exception('Configuration mode not known! Only CC or CV allowed')

    ttime = 0.0
    etime= 0.0 # Ellapsed time
    itime = 0.0
    start = True
    ############  LOGGING THE DATA ###################################
    # Opening the file to save the data
    filename = os.path.join(folder, fname + '.txt')  
    if not os.path.isfile(filename):
        with open(filename,'a') as f:
            f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage', 'Absolute time', 'Temperature'))
            f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('i','s','A', 'V', 's','C'))
    
    if gs.MEASUREMENT_ON:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        with open(filename,'a') as f:
            f.write('{}\n'.format(timestamp))               

    i = 0 # Step counter

    if gs.MEASUREMENT_ON:
        if gs.MODE == 'CC':
            ky2400.mode_ifix_setcurr(value / 1000.0, curr_max=0.1, curr_min= 0.00)
        else:
            ky2400.mode_vfix_setvolt(value)
        ky2400.outpon()
        
    while etime < rtime and gs.MEASUREMENT_ON:
        try:
            
            time1 = time()
            [mvoltage, mcurrent, _ , ttime, _ ] = ky2400.read()

#            assert not ky2400.check_volt_compliance(), 'Compliance reached!'
            if not start:
                etime = ttime - itime
            else:
                itime =  ttime
                start = False

            with open(pjoin(ABSOLUTE_PATH, 'temp/temp.dat')) as f1:
                temperature = float(f1.read())
                
            with open(filename,'a') as f:
                f.write(('{:^5d}\t' +5*'{:^10.6f}\t' + '\n').format(i,etime, mcurrent, mvoltage,ttime, temperature))
            i += 1
            
            gs.ETIME.append(datetime.datetime.now())
            gs.CURRENT.append(mcurrent)
            gs.VOLTAGE.append(mvoltage)
                
                    
            if gs.SET_VALUE == value:
                pass
            else:
                if gs.MODE == 'CC':
                    ky2400.mode_ifix_setcurr(gs.SET_VALUE / 1000.0,curr_max=0.1, curr_min= 0.00)
                else:
                    ky2400.mode_vfix_setvolt(gs.SET_VALUE)
                    
                value = gs.SET_VALUE
                
            if dt_fix:
                sleeping_time = dt
            else:
                sleeping_time = dt_calc(etime)
                    

            while (time() - time1) < sleeping_time and gs.MEASUREMENT_ON:
                sleep(0.01)
                
        except KeyboardInterrupt:
            # In case of error turn off the source anyway and stop the program
            print('Programm interrupted in a safe way\n')
            if interrupt_measurement:
                print('Measurement stopped, but sourcemeter still on\n')
            else:
                ky2400.outpoff()
                f.close()
            break
        except Exception as e:
            # In case of ANY error turn off the source anyway and stop the program while printing the error
            print(e)
            ky2400.outpoff()
            break

    if interrupt_measurement:
        ky2400.outpoff()