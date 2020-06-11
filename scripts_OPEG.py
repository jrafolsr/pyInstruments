
# coding: utf-8
# Library that depends on the pyLab library and that contains the main program/functions
# for driving the LEC devices at diferent modes.

import numpy as np
from time import sleep, time
import pyLab # This the module I created
import datetime
import os
import global_settings_ivl as gsivl
today = datetime.date.today().strftime("%Y%m%d")


def run_fix_current(current, rtime = np.inf, dt = 0.25,\
                    folder = '.\\', fname = 'voltage-time-data',\
                    resource = 'GPIB0::24::INSTR', term = 'FRONT',\
                    fw = False, beeper = True, cmpl = 21.0,\
                    Ncount = 1, aver = False):
    """Here goes the documentation of the function
    Mandatory arguments:
        - current: current in mA
    Optional arguments:
        - rtime: running time of the experiment, infinit by default
        - dt: time inverval between measueements
        - folder: folder path where to save the file, abs o relative, current directory by default.
        - fname: filename where to save the data. Always append if the file already exists
        - resource: resource name for the Keithley2400, default is 'GPIB0::24::INSTR'
        - term: either FRONT (default) or REAR
        - other, to be filled
    
    """
    
    # First, we create an instance of a ktly24XX instrument class with the resource
    # passed as an argument
    ky2400 = pyLab.ktly20XX(resource)
    ky2400.mode_ifix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount=Ncount, aver = aver)
    
    
    # Initializing some other values and figure
    get_ipython().run_line_magic('matplotlib', 'notebook')
    figure = pyLab.figure(ylabel = 'Voltage (V)', xlabel= 'Time (s)', title = 'Voltage-Time plot')
    ptime = []
    pvolt = []

    Nsteps = 2000
    
    i = 0
    
    # Opening the file to save the data
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    filename = os.path.join(folder,today + '_' + fname + '.txt')
    
    if not os.path.isfile(filename):
        f=open(filename,'a')
        f.write(('# {:^5}\t'+3*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage'))
        f.write(('# {:^5}\t'+3*'{:^12}\t' + '\n').format('i','s','mA','V'))
    else:
        f=open(filename,'a')
        f.write('# {}\n'.format(timestamp))
    
    
    ky2400.mode_ifix_setcurr(current / 1000.0,curr_max=0.1, curr_min= 0.0)
    ky2400.outpon()
    ttime = 0.0
    start = True
    stime = time()
    while ttime < rtime:
        try:
            
            [voltage, current, _ , ttime, _ ] = ky2400.read()
            if not start:
                ptime.append(ttime - itime)
            else:
                itime =  ttime
                ptime.append(0.0)
                start = False
            pvolt.append(voltage)
    
            # This creates an updating figure (by erasing the axis) It slows down the performance but still enough
            # for this application
            figure.update_lines(ptime, [pvolt])
            figure.update_axes(0)
            figure.update_axes(1)
    
            f.write(('{:^5d}\t' +3*'{:^12.10f}\t' + '\n').format(i,ttime - itime, current,voltage))
    
            i += 1
            # Safety line in order not to plot infinit values and charge the memnory
            if i % Nsteps == 0:
                ptime = [ptime[-1]]
                pvolt = [pvolt[-1]]
                i = 0
                figure.ax.set_xlim(ptime[-1],ptime[-1]*1.5)
                figure.ax.set_ylim(pvolt[-1]*0.99,pvolt[-1]*1.01)
            
            sleep(dt - (time() - stime) % dt )
        except KeyboardInterrupt:
            # In case of error turn off the source anyway and stop the program
            print('Programm interrupted in a safe way\n')
            break
        except Exception as e:
            # In case of ANY error turn off the source anyway and stop the program while printing the error
            print()
            break
    
    ky2400.outpoff()
    f.close()
                    
def run_fix_voltage(voltage, rtime = np.inf, dt = 0.25,\
                    folder = '.\\', fname = 'current-time-data',\
                    resource = 'GPIB0::24::INSTR', term = 'FRONT',\
                    fw = False, beeper = True, cmpl = 0.05,\
                    Ncount = 1, aver = False):
    """Here goes the documentation of the function
    Mandatory arguments:
        - voltage: voltage in V
    Optional arguments:
        - rtime: running time of the experiment, infinit by default
        - dt: time inverval between measurements
        - folder: folder path where to save the file, abs o relative, current directory by default.
        - fname: filename where to save the data. Always append if the file already exists
        - resource: resource name for the Keithley2400, default is 'GPIB0::24::INSTR'
        - term: either FRONT (default) or REAR
        - other, to be filled
    
    """
    
    # First, we create an instance of a ktly24XX instrument class with the resource
    # passed as an argument
    ky2400 = pyLab.ktly20XX(resource)
    ky2400.mode_vfix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount, aver = aver)
    
    
    # Initializing some other values and figure
    get_ipython().run_line_magic('matplotlib', 'notebook')
    figure = pyLab.figure(ylabel = 'Current (mA)', xlabel= 'Time (s)', title = 'Current-Time plot')
    ptime = []
    pvalue = []

    Nsteps = 2000
    
    i = 0
    
    # Opening the file to save the data
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    filename = os.path.join(folder,today + '_' + fname + '.txt')
    
    if not os.path.isfile(filename):
        f=open(filename,'a')
        f.write(('# {:^5}\t'+3*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage'))
        f.write(('# {:^5}\t'+3*'{:^12}\t' + '\n').format('i','s','mA','V'))
    else:
        f=open(filename,'a')
        f.write('# {}\n'.format(timestamp))
    
    
    ky2400.mode_vfix_setvolt(voltage)
    ky2400.outpon()
    ttime = 0.0
    start = True
    stime = time()
    itime = 0.0
    while ttime < rtime:
        try:
            
            [voltage, current, _ , ttime, _ ] = ky2400.read()
            if not start:
                ptime.append(ttime - itime)
            else:
                itime =  ttime
                ptime.append(0.0)
                start = False
            pvalue.append(current * 1000)
    
            # This creates an updating figure (by erasing the axis) It slows down the performance but still enough
            # for this application
            figure.update_lines(ptime, [pvalue])
            figure.update_axes(0)
            figure.update_axes(1)
    
            f.write(('{:^5d}\t' +3*'{:^12.10f}\t' + '\n').format(i,ttime - itime, current,voltage))
    
            i += 1
            # Safety line in order not to plot infinit values and charge the memnory
            if i % Nsteps == 0:
                ptime = [ptime[-1]]
                pvalue = [pvalue[-1]]
                i = 0
                figure.ax.set_xlim(ptime[-1],ptime[-1]*1.5)
                figure.ax.set_ylim(pvalue[-1]*0.99,pvalue[-1]*1.01)
            
            sleep(dt - (time() - stime) % dt )
        except KeyboardInterrupt:
            # In case of error turn off the source anyway and stop the program
            print('Programm interrupted in a safe way\n')
            break
        except Exception as e:
            # In case of ANY error turn off the source anyway and stop the program while printing the error
            print()
            break
    
    ky2400.outpoff()
    f.close()
    

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

def ivl_setup(current, rtime = np.inf, dt = 0.25,\
                    folder = '.\\', fname = 'voltage-time-data',\
                    resource1 = 'GPIB0::24::INSTR', term = 'FRONT',\
                    resource2 = 'GPIB0::23::INSTR',\
                    fw = False, beeper = True, cmpl = 21.0,\
                    Ncount = 1, aver = False, nplc = 1.0,
                    config = True, interrupt_measurement = False,
                    dt_fix = True):
    """Here goes the documentation of the function
    Mandatory arguments:
        - current: current in mA
    Optional arguments:
        - rtime: running time of the experiment, infinit by default
        - dt: time inverval between measueements.
        - folder: folder path where to save the file, abs o relative, current directory by default.
        - fname: filename where to save the data. Always append if the file already exists
        - resource1: resource name for the sourcemeter Keithley24XX, default is 'GPIB0::24::INSTR'
        - resource2: resource name for the multimeter, default is 'GPIB0::23::INSTR'
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
    
    # First, we create an instance of a ktly24XX instrument class with the resource passed as an argument and later we configure (or not) the resource considering it is a Keithley24XX family
    ky2400 = pyLab.ktly20XX(resource1)
    mult = pyLab.keysight34461A(resource2) # Creating the object for the multimeter
    if config:
        ky2400.mode_ifix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount,\
                                   nplc = nplc, aver = aver)
   
############# MULTIMETER #################################    
        
        mult.config_volt(rang = 5.0, nplc = nplc, count = Ncount)  # Configure the multimeter
    
############ INDICATORS FOR THE JUPYTER NOTEBOOK ##############################   
    readings, ui = pyLab.CreateIndicators(['Voltage', 'Voltage'],[0.0]*2,['LEC', 'PhD'])
    
############ Initializing some  values and figure ###########################
    get_ipython().run_line_magic('matplotlib', 'notebook')
    figure = pyLab.figure(ndatasets=2,ylabel = 'Voltage (V)', xlabel= 'Time (s)', title = 'Voltage-Time plot')
    ptime = []
    pvolt = []
    pdiode = []

    Nsteps = 2000 # Maxmimum number of values of the array to print
    
############  LOGGING THE DATA ###################################
    # Opening the file to save the data
    filename = os.path.join(folder,today + '_' + fname + '.txt')  
    if not os.path.isfile(filename):
        f = open(filename,'a')
        f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage', 'Photocurrent_volt(V)', 'Absolute time(s)'))
        f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('i','s','A','V', 'V', 's'))
    else:
        f = open(filename,'a')
########## PERFORMING FIRST MEASUREMENTS ############################
    # First measruementes without running the LEC 
    if config:
        ky2400.mode_ifix_setcurr(0.0 / 1000.0, curr_max=0.1, curr_min= -0.001)
        ky2400.outpon()
    
    ttime = 0.0
    etime= 0.0 # Ellapsed time
    itime = 0.0
    start = True
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    f.write('# {}\n'.format(timestamp))
    stime = time()
    zero_current_time = 2.0
    flag_scurr = False # Flag to control if the current has been set or not.
    i = 0 # Step counter
    k = 0
    
    # Add this function to sequentally update the time interval of the measurement
    if dt_fix:
        sleeping_time = dt
    else:
        sleeping_time = dt_calc(etime)
    
    while etime < rtime:
        try:          
            [voltage, mcurrent, _ , ttime, _ ] = ky2400.read()
            voltage_ph = mult.read().mean()
#            assert not ky2400.check_volt_compliance(), 'Compliance reached!'
            if not start:
                etime = ttime - itime
                ptime.append(etime)
            else:
                itime =  ttime
                ptime.append(0.0)
                start = False
            pvolt.append(voltage)
            pdiode.append(voltage_ph)
    
            # This creates an updating figure (by erasing the axis) It slows down the performance but still enough
            # for this application
            figure.update_lines(ptime, [pvolt, pdiode])
            figure.update_axes(0)
            figure.update_axes(1)        
    
            f.write(('{:^5d}\t' +5*'{:^12.10f}\t' + '\n').format(k,etime, mcurrent,voltage, voltage_ph,ttime))
            
            readings[0].value = str(voltage)
            readings[1].value = str(voltage_ph)
    
            i += 1
            k += 1
            # Safety line in order not to plot infinit values and charge the memnory
            if i % Nsteps == 0:
                ptime = [ptime[-1]]
                pvolt = [pvolt[-1]]
                pdiode = [pdiode[-1]]
                i = 0
                figure.update_axes(0, (ptime[-1],ptime[-1] + 10*sleeping_time))
                figure.update_axes(1, (pvolt[-1]*0.95,pvolt[-1]*1.05))
            
            if (ttime - itime) >=  zero_current_time and config and not flag_scurr:
                ky2400.mode_ifix_setcurr(current / 1000.0,curr_max=0.1, curr_min= 0.00)
                flag_scurr = True
            
            if dt_fix:
                sleeping_time = dt
            else:
                sleeping_time = dt_calc(etime)
                    
            sleep(sleeping_time - (time() - stime) % sleeping_time )
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
            f.close()
            break
    if not interrupt_measurement:
        ky2400.outpoff()
        f.close()
        


def ivl_setup_v2(current, rtime = np.inf, dt = 0.25,\
                    folder = '.\\', fname = 'voltage-time-data',\
                    resource1 = 'GPIB0::24::INSTR', term = 'FRONT',\
                    resource2 = 'GPIB0::23::INSTR',\
                    fw = False, beeper = True, cmpl = 21.0,\
                    Ncount = 1, aver = False, nplc = 1.0,
                    config = True, interrupt_measurement = False,
                    dt_fix = True):
    """Standalone version of the ivl_setup, to be runned directly either from the terminal prompt or from a script.
    Mandatory arguments:
        - current: current in mA
    Optional arguments:
        - rtime: running time of the experiment, infinit by default
        - dt: time inverval between measueements.
        - folder: folder path where to save the file, abs o relative, current directory by default.
        - fname: filename where to save the data. Always append if the file already exists
        - resource1: resource name for the sourcemeter Keithley24XX, default is 'GPIB0::24::INSTR'
        - resource2: resource name for the multimeter, default is 'GPIB0::23::INSTR'
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
    
    # First, we create an instance of a ktly24XX instrument class with the resource passed as an argument and later we configure (or not) the resource considering it is a Keithley24XX family
    ky2400 = pyLab.ktly20XX(resource1)
    mult = pyLab.keysight34461A(resource2) # Creating the object for the multimeter
    if config:
        ky2400.mode_ifix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount,\
                                   nplc = nplc, aver = aver)
   
############# MULTIMETER #################################    
        
        mult.config_volt(rang = 5.0, nplc = nplc, count = Ncount)  # Configure the multimeter
    
   
############ Initializing some  values and figure ###########################
    Nsteps = 200 # Maxmimum number of values of the array to print
    ptime = np.linspace(0,Nsteps,Nsteps, False)
    pvolt = np.zeros(len(ptime))
    pdiode = np.zeros(len(ptime))
    lines = None

    
    
############  LOGGING THE DATA ###################################
    # Opening the file to save the data
    filename = os.path.join(folder,today + '_' + fname + '.txt')  
    if not os.path.isfile(filename):
        f = open(filename,'a')
        f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage', 'Photocurrent_volt(V)', 'Absolute time(s)'))
        f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('i','s','A','V', 'V', 's'))
    else:
        f = open(filename,'a')
########## PERFORMING FIRST MEASUREMENTS ############################
    # First measruementes without running the LEC 
    if config:
        ky2400.mode_ifix_setcurr(0.0 / 1000.0, curr_max=0.1, curr_min= -0.001)
        ky2400.outpon()
    
    ttime = 0.0
    etime= 0.0 # Ellapsed time
    itime = 0.0
    start = True
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    f.write('# {}\n'.format(timestamp))
    stime = time()
    zero_current_time = 2.0
    flag_scurr = False # Flag to control if the current has been set or not.
    flag_ch_cmpl = False # Just to check if the compliance has been change after x seconds
    i = 0 # Step counter
    k = 0
    
    # Add this function to sequentally update the time interval of the measurement
    if dt_fix:
        sleeping_time = dt
    else:
        sleeping_time = dt_calc(etime)
    
    while etime < rtime:
        try:
            time1 = time()
            [voltage, mcurrent, _ , ttime, _ ] = ky2400.read()
            voltage_ph = mult.read().mean()
#            assert not ky2400.check_volt_compliance(), 'Compliance reached!'
            if not start:
                etime = ttime - itime
            else:
                itime =  ttime
                start = False

            pvolt[-1] = voltage
            pdiode[-1] = voltage_ph
    
            f.write(('{:^5d}\t' +5*'{:^12.10f}\t' + '\n').format(k,etime, mcurrent,voltage, voltage_ph,ttime))
            
    
            i += 1
            k += 1

            lines = pyLab.live_plotter(ptime,[pvolt, pdiode],lines, title = 'IVL characterisation', ylabel = 'Voltage (V)')
            pvolt = np.append(pvolt[1:],0.0)
            pdiode = np.append(pdiode[1:],0.0)
            
            if not flag_ch_cmpl:
                if (time() - stime) > 300:
                    ky2400.inst.write(":SENS:VOLT:PROT 21")    # Set 21V compliance limit.
                    flag_ch_cmpl = True
            
            if (ttime - itime) >=  zero_current_time and config and not flag_scurr:
                ky2400.mode_ifix_setcurr(current / 1000.0,curr_max=0.1, curr_min= 0.00)
                flag_scurr = True
            
            if dt_fix:
                sleeping_time = dt
            else:
                sleeping_time = dt_calc(etime)
                    

            while (time() - time1) < sleeping_time:
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
            f.close()
            break
    if not interrupt_measurement:
        ky2400.outpoff()
        f.close()
        
def ivl_setup_gui(current, window, rtime = np.inf, dt = 0.25,\
                    folder = '.\\', fname = 'voltage-time-data',\
                    resource1 = 'GPIB0::24::INSTR', term = 'FRONT',\
                    resource2 = 'GPIB0::23::INSTR',\
                    fw = False, beeper = True, cmpl = 21.0,\
                    Ncount = 1, aver = False, nplc = 1.0,
                    config = True, interrupt_measurement = False,
                    dt_fix = True):
    """Standalone version of the ivl_setup, to be runned directly either from the terminal prompt or from a script.
    Mandatory arguments:
        - current: current in mA
        - window to which we are plotting, as it is the gui version
    Optional arguments:
        - rtime: running time of the experiment, infinit by default
        - dt: time inverval between measueements.
        - folder: folder path where to save the file, abs o relative, current directory by default.
        - fname: filename where to save the data. Always append if the file already exists
        - resource1: resource name for the sourcemeter Keithley24XX, default is 'GPIB0::24::INSTR'
        - resource2: resource name for the multimeter, default is 'GPIB0::23::INSTR'
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
    
    # First, we create an instance of a ktly24XX instrument class with the resource passed as an argument and later we configure (or not) the resource considering it is a Keithley24XX family
    ky2400 = pyLab.ktly20XX(resource1)
    mult = pyLab.keysight34461A(resource2) # Creating the object for the multimeter
    if config:
        ky2400.mode_ifix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount,\
                                   nplc = nplc, aver = aver)
   
############# MULTIMETER #################################    
        
        mult.config_volt(rang = 5.0, nplc = nplc, count = Ncount)  # Configure the multimeter
    
   
############ Initializing some  values and figure ###########################
    Nsteps = 200 # Maxmimum number of values of the array to print
    ptime = np.linspace(0,Nsteps,Nsteps, False)
    pvolt = np.zeros(len(ptime))
    pdiode = np.zeros(len(ptime))
    lines = None

    
    
############  LOGGING THE DATA ###################################
    # Opening the file to save the data
    filename = os.path.join(folder,today + '_' + fname + '.txt')  
    if not os.path.isfile(filename):
        f = open(filename,'a')
        f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage', 'Photocurrent_volt(V)', 'Absolute time(s)'))
        f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('i','s','A','V', 'V', 's'))
    else:
        f = open(filename,'a')
########## PERFORMING FIRST MEASUREMENTS ############################
    # First measruementes without running the LEC 
    if config:
        ky2400.mode_ifix_setcurr(0.0 / 1000.0, curr_max=0.1, curr_min= -0.001)
        ky2400.outpon()
    
    ttime = 0.0
    etime= 0.0 # Ellapsed time
    itime = 0.0
    start = True
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    f.write('# {}\n'.format(timestamp))
    stime = time()
    zero_current_time = 2.0
    flag_scurr = False # Flag to control if the current has been set or not.

    i = 0 # Step counter
    k = 0
    
    
    while etime < rtime:
        try:
            time1 = time()
            [voltage, mcurrent, _ , ttime, _ ] = ky2400.read()
            voltage_ph = mult.read().mean()
#            assert not ky2400.check_volt_compliance(), 'Compliance reached!'
            if not start:
                etime = ttime - itime
            else:
                itime =  ttime
                start = False

            pvolt[-1] = voltage
            pdiode[-1] = voltage_ph
    
            f.write(('{:^5d}\t' +5*'{:^12.10f}\t' + '\n').format(k,etime, mcurrent,voltage, voltage_ph,ttime))
            
    
            i += 1
            k += 1

            lines = pyLab.live_plotter(ptime,[pvolt, pdiode],lines, title = 'IVL characterisation', ylabel = 'Voltage (V)')
            pvolt = np.append(pvolt[1:],0.0)
            pdiode = np.append(pdiode[1:],0.0)

                    
            if (ttime - itime) >=  zero_current_time and config and not flag_scurr:
                ky2400.mode_ifix_setcurr(current / 1000.0,curr_max=0.1, curr_min= 0.00)
                flag_scurr = True
            
            if dt_fix:
                sleeping_time = dt
            else:
                sleeping_time = dt_calc(etime)
            
            #sleeping_time = sleeping_time - (time() - stime) % sleeping_time
            while (time() - time1) < sleeping_time:
                sleep(0.01)
                window.update()
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
            f.close()
            break
    if not interrupt_measurement:
        ky2400.outpoff()
        f.close()
        
def ivl_setup_daq(current, rtime = np.inf, dt = 0.25,\
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
    Mandatory arguments:
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
    
    # First, we create an instance of a ktly24XX instrument class with the resource passed as an argument and later we configure (or not) the resource considering it is a Keithley24XX family
    ky2400 = pyLab.ktly20XX(resource1)
    
    if config:
        ky2400.mode_ifix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount,\
                                   nplc = nplc, aver = aver)
   
    usb6009 = pyLab.daq(device,adqTime,adqFreq,list_channels,rang_channels, mode = mode, terminalConfig = terminalConfig)
############ Initializing some  values and figure ###########################
    Nsteps = 200 # Maxmimum number of values of the array to print
    ptime = np.linspace(0,Nsteps,Nsteps, False)
    pvolt = np.zeros(len(ptime))
    pdiode = np.zeros(len(ptime))
    lines = None

    
    
############  LOGGING THE DATA ###################################
    # Opening the file to save the data
    filename = os.path.join(folder,today + '_' + fname + '.txt')  
    if not os.path.isfile(filename):
        with open(filename,'a') as f:
            f = open(filename,'a')
            f.write(('# {:^5}\t'+6*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage', 'Photocurrent_volt', 'Absolute time', 'Temperature'))
            f.write(('# {:^5}\t'+6*'{:^12}\t' + '\n').format('i','s','A','V', 'V', 's','C'))

########## PERFORMING FIRST MEASUREMENTS ############################
    # First measruementes without running the LEC 
    if config:
        ky2400.mode_ifix_setcurr(0.0 / 1000.0, curr_max=0.1, curr_min= -0.001)
        ky2400.outpon()
    
    ttime = 0.0
    etime= 0.0 # Ellapsed time
    itime = 0.0
    start = True
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
    with open(filename,'a') as f:
        f.write('# {}\n'.format(timestamp))
    stime = time()
    zero_current_time = 2.0
    flag_scurr = False # Flag to control if the current has been set or not.
    flag_ch_cmpl = False # Just to check if the compliance has been change after x seconds
    i = 0 # Step counter
    k = 0
    
    # Add this function to sequentally update the time interval of the measurement
    if dt_fix:
        sleeping_time = dt
    else:
        sleeping_time = dt_calc(etime)
    
    while etime < rtime:
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

            pvolt[-1] = voltage
            pdiode[-1] = voltage_ph*1.0
            # Snippet to read the temperature of the PID
            with open(r'..\Python Scripts\temp\temp.dat') as f1:
                temperature = float(f1.read())
            with open(filename,'a') as f:
                f.write(('{:^5d}\t' +6*'{:^12.10f}\t' + '\n').format(k,etime, mcurrent,voltage, voltage_ph,ttime, temperature))
    
            i += 1
            k += 1

            lines = pyLab.live_plotter(ptime,[pvolt, pdiode],lines, title = 'IVL characterisation', ylabel = 'Voltage (V)')
            pvolt = np.append(pvolt[1:],0.0)
            pdiode = np.append(pdiode[1:],0.0)
            
            if not flag_ch_cmpl:
                if (time() - stime) > 300:
                    ky2400.inst.write(":SENS:VOLT:PROT 21")    # Set 21V compliance limit.
                    flag_ch_cmpl = True
            
            if (ttime - itime) >=  zero_current_time and config and not flag_scurr:
                ky2400.mode_ifix_setcurr(current / 1000.0,curr_max=0.1, curr_min= 0.00)
                flag_scurr = True
            
            if dt_fix:
                sleeping_time = dt
            else:
                sleeping_time = dt_calc(etime)
                    

            while (time() - time1) < sleeping_time:
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
            f.close()
            usb6009.clear()
            break
    if not interrupt_measurement:
        ky2400.outpoff()
        f.close()
        
        
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
    ky2400 = pyLab.ktly20XX(resource1)
    
    gsivl.SET_CURRENT = current
    
    if gsivl.CONFIG_STATUS:
        ky2400.mode_ifix_configure(fw = fw,beeper = beeper, term = term, cmpl = cmpl, Ncount = Ncount,\
                                   nplc = nplc, aver = aver)

        
    usb6009 = pyLab.daq(device,adqTime,adqFreq,list_channels,rang_channels, mode = mode, terminalConfig = terminalConfig)

        
    
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
    if gsivl.MEASUREMENT_ON:
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
    
    if gsivl.MEASUREMENT_ON: 
        ky2400.mode_ifix_setcurr(current / 1000.0,curr_max=0.1, curr_min= 0.00)
        ky2400.outpon()
    else: ky2400.outpoff()
    
    max_length = 500 # Max. length of the global data
    
    while etime < rtime and gsivl.MEASUREMENT_ON:
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
            
            total_length = len(gsivl.ETIME)
            
            if total_length < max_length or total_length == 0:
                gsivl.ETIME.append(datetime.datetime.now())
                gsivl.CURRENT.append(mcurrent)
                gsivl.VOLTAGE.append(voltage)
                gsivl.LUMINANCE.append(voltage_ph)
            else:
                gsivl.ETIME = gsivl.ETIME[1:] + [datetime.datetime.now()]
                gsivl.CURRENT =  gsivl.CURRENT[1:] + [mcurrent]
                gsivl.VOLTAGE = gsivl.VOLTAGE[1:] + [voltage]
                gsivl.LUMINANCE =  gsivl.LUMINANCE[1:] + [voltage_ph]
                
            if not flag_ch_cmpl:
                if (time() - stime) > 300:
                    ky2400.inst.write(":SENS:VOLT:PROT 21")    # Set 21V compliance limit.
                    flag_ch_cmpl = True
                    
            if gsivl.SET_CURRENT == current:
                pass
            else:
                ky2400.mode_ifix_setcurr(gsivl.SET_CURRENT / 1000.0,curr_max=0.1, curr_min= 0.00)
                current = gsivl.SET_CURRENT
                
            if dt_fix:
                sleeping_time = dt
            else:
                sleeping_time = dt_calc(etime)
                    

            while (time() - time1) < sleeping_time and gsivl.MEASUREMENT_ON:
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