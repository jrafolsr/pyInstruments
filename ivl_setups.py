
# coding: utf-8
# Library that depends on the pyLab library and that contains the main program/functions
# for driving the LEC devices at diferent modes.

import numpy as np
from time import sleep, time
from .instruments import keithley24XX, daq # This the module I created
import datetime
import os
from . import global_settings_ivl as gs
today = datetime.date.today().strftime("%Y%m%d")
from collections import deque

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


def ivl_setup_cc(current, rtime = np.inf, dt = 0.25,\
                    folder = '.\\', fname = 'voltage-time-data',\
                    resource1 = 'GPIB0::24::INSTR', term = 'FRONT',\
                    fw = False, beeper = True, cmpl = 21.0,\
                    Ncount = 1, aver = False, nplc = 1.0,
                    config = True, interrupt_measurement = False,dt_fix = True,\
                    device = 'Dev1',\
                    adqTime = 0.05, adqFreq = 10000, list_channels  = [0],\
                    rang_channels = [10], mode = 'FiniteSamps',\
                    terminalConfig = 'SE'):
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
        - dt_fix: the time interval is fixed. It set to false, then it uses the time interval from the function dt_calc()
    """
    # Configuration only done if not done before
    ky2400 = keithley24XX(resource1)
    
    gs.SET_CURRENT = current
    
    if gs.CONFIG_STATUS:
        ky2400.mode_ifix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount,\
                                   nplc = nplc, aver = aver)

        
    usb6009 = daq(device,adqTime,adqFreq,list_channels,rang_channels, mode = mode, terminalConfig = terminalConfig)

        
    
    ttime = 0.0
    etime= 0.0 # Ellapsed time
    itime = 0.0
    start = True
    ############  LOGGING THE DATA ###################################
    # Opening the file to save the data
    filename = os.path.join(folder,today + '_' + fname + '.txt')  
    if not os.path.isfile(filename):
        with open(filename,'a') as f:
            f.write(('# {:^5}\t'+6*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage', 'Photocurrent_volt', 'Absolute time', 'Temperature'))
            f.write(('# {:^5}\t'+6*'{:^12}\t' + '\n').format('i','s','A','V', 'V', 's','C'))
    if gs.MEASUREMENT_ON:
        # Obtaining and saving offset for photodiode voltage
        usb6009.start()
        voltage_ph = usb6009.read_analog().mean(axis = 0)[0]
        usb6009.stop()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        with open(filename,'a') as f:
            f.write('# {}\n'.format(timestamp))
            f.write(('# Offset photodiode: {:^12.10f}' + '\n').format(voltage_ph))             
                
    stime = time()

    
    flag_ch_cmpl = False # Just to check if the compliance has been change after x seconds
    i = 0 # Step counter
    
    if gs.MEASUREMENT_ON: 
        ky2400.mode_ifix_setcurr(current / 1000.0,curr_max=0.1, curr_min= 0.00)
        ky2400.outpon()
    else: ky2400.outpoff()
        
    while etime < rtime and gs.MEASUREMENT_ON:
        try:
            
            time1 = time()
            [voltage, mcurrent, _ , ttime, _ ] = ky2400.read()
            usb6009.start()
            voltage_ph = usb6009.read_analog().mean(axis = 0)[0]
            usb6009.stop()
#            assert not ky2400.check_volt_compliance(), 'Compliance reached!'
            if not start:
                etime = ttime - itime
            else:
                itime =  ttime
                start = False

            with open(r'.\temp\temp.dat') as f1:
                temperature = float(f1.read())
            with open(filename,'a') as f:
                f.write(('{:^5d}\t' +6*'{:^12.10f}\t' + '\n').format(i,etime, mcurrent,voltage, voltage_ph,ttime, temperature))
            i += 1
            
            gs.ETIME.append(datetime.datetime.now())
            gs.CURRENT.append(mcurrent)
            gs.VOLTAGE.append(voltage)
            gs.LUMINANCE.append(voltage_ph)

                
            if not flag_ch_cmpl:
                if (time() - stime) > 300:
                    ky2400.inst.write(":SENS:VOLT:PROT 21")    # Set 21V compliance limit.
                    flag_ch_cmpl = True
                    
            if gs.SET_CURRENT == current:
                pass
            else:
                ky2400.mode_ifix_setcurr(gs.SET_CURRENT / 1000.0,curr_max=0.1, curr_min= 0.00)
                current = gs.SET_CURRENT
                
            if dt_fix:
                sleeping_time = dt
            else:
                sleeping_time = dt_calc(etime)
                    

            while (time() - time1) < sleeping_time and gs.MEASUREMENT_ON:
                sleep(0.01)
                
        except KeyboardInterrupt:
            # In case of error turn off the source anyway and stop the program
            print('Programm interrupted in a safe way\n')
            usb6009.clear()
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
            usb6009.clear()
            break

    if not interrupt_measurement:
        ky2400.outpoff()