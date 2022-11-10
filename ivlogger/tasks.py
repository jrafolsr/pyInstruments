# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 10:37:57 2020

@author: OPEGLAB
"""


# coding: utf-8
# Library that depends on the pyLab library and that contains the main program/functions
# for driving the LEC devices at diferent modes.

import numpy as np
from time import sleep, monotonic
from pyInstruments.instruments import keithley24XX # This the module I created
import datetime
from collections import deque
from pathlib import Path
from pyInstruments import __file__ as module_folder

tempfile = Path(module_folder).parent / Path('temp/temp.dat')

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
 
class IVLoggerTask(object):
    def __init__(self, resource = None, folder = Path('.\\'), filename = 'voltage-time-data',\
                  mode = 'CC', term = 'FRONT', fw = False, beeper = True, cmpl = 21.0, Ncount = 1,\
                  aver = False, nplc = 1.0, config_flag = True):
        """
        Parameters
        ----------
        resource : str, optional
            The resource name for the sourcemeter Keithley24XX, default is 'GPIB0::24::INSTR'. The default is 'GPIB0::24::INSTR'.
        folder : str, optional
            Folder where to save the data, abs o relative. The default is '.\'.
        filename : bool, optional
            Filename where to save the data. Always append if the file already exists. The default is 'voltage-time-data'.
        mode : str, optional
            Input 'CC' or 'CV' for constant current/voltage modes. The default is 'CC'.
        term : str, optional
            Output terminal for the Keithley, only 'FRONT' or 'REAR' is accepted. The default is 'FRONT'.
        fw : bool, optional
            Activate the four-wire measurement. The default is False.
        beeper : bool, optional
            Activate the beeper. The default is True.
        cmpl : float, optional
            Compliance for the sourcemeter (either in V or A, depending on the mode). The default is 21.0.
        Ncount : int, optional
            Number of samples to ask the sourcemeter. The default is 1.
        aver : bool, optional
            Whether to average the number of samples given for Ncount. The default is False.
        nplc : float, optional
            Number of pulse light cycles to integrate. The default is 1.0.
        config_flag : bool, optional
            Whether to configurate or not the sourcemeter. The default is True.

        Returns
        -------
        None.

        """

        self.max_length = 500
        self.time = deque([], self.max_length )
        self.voltage = deque([], self.max_length )
        self.intensity =  deque([], self.max_length )
        self.resource = resource
        self.folder = folder
        self.filename = filename
        self.mode = mode
        self.configuration = dict(term = term, fw = fw, beeper = beeper, cmpl = cmpl, Ncount = Ncount, aver = aver, nplc = nplc)
        self.config_flag = config_flag
        self.value = 0.00
        
    def start_instrument(self):
        """
        Powers on the instrument.
        
        """
        
        # Opening the resource only done if not done before
        if self.resource is  None:
            raise ValueError('The sourcemeter resource has not been defined. Please define it throught the resource attribute')
            
        self.keithley = keithley24XX(self.resource)

        if self.config_flag:
            if self.mode == 'CC':
                print('INFO: Instrument configured in CC mode.')
                self.keithley.mode_ifix_configure(**self.configuration)
            elif self.mode == 'CV':
                print('INFO: Instrument configured in CV mode.')
                self.keithley.mode_vfix_configure(**self.configuration)
            else:
                raise ValueError('ERROR: Configuration mode not known! Only CC or CV allowed')
            

    def run(self, value, runtime = np.inf, dt = 0.25, interrupt_measurement = True, dt_fix = True, external_variable = ('Temperature', 'C')):
        """
        Parameters
        ----------
        value : float
            Current (in mA) or voltage (V) setpoint value.
        runtime : float, optional
            Running time of the experiment in seconds. The default is np.inf.
        dt : float, optional
            Rime inverval between measurements. The default is 0.25.
        interrupt_measurement : bool, optional
            If True, only the data logging will be interrupted, the sourcemetert will continue feeding the current/voltage. The default is True.
        dt_fix : bool, optional
            If True, the time interval is fixed. If set to false, then it uses the time interval from the function dt_calc(). The default is True.
        external_variable : tuple, optional
            Tuple of len 2 with the name and units of the external vairable save at temp.dat. The default is ('Temperature', 'C').

        """
        
        ############  LOGGING THE DATA ###################################
        # Opening the file to save the data
        filename = Path(self.folder) / (self.filename + '.txt')  
        if not filename.exists():
            with open(filename,'a') as f:
                f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('Step','Time','Current','Voltage', 'Absolute time', external_variable[0]))
                f.write(('# {:^5}\t'+5*'{:^12}\t' + '\n').format('i','s','A', 'V', 's',external_variable[1]))
        

        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        with open(filename,'a') as f:
            f.write('{}\n'.format(timestamp))               

        if self.mode == 'CC':
              self.keithley.mode_ifix_setcurr(value / 1000.0, curr_max = 0.1, curr_min= 0.00)
        else:
              self.keithley.mode_vfix_setvolt(value)
        
        ttime = 0.0
        etime= 0.0 # Ellapsed time
        itime = 0.0
        start = True  
        i = 0 # Step counter
        
        self.keithley.outpon()
        self.running = True

        while etime < runtime and self.running:
            try:
                
                time1 = monotonic()
                [mvoltage, mcurrent, _ , ttime, _ ] =   self.keithley.read()
    
    #            assert not   self.keithley.check_volt_compliance(), 'Compliance reached!'
                if not start:
                    etime = ttime - itime
                else:
                    itime =  ttime
                    start = False
                    
                with open(tempfile) as f:
                    external_value = float(f.read())
                    
                with open(filename,'a') as f:
                    f.write(('{:^5d}\t' +5*'{:^10.6f}\t' + '\n').format(i,etime, mcurrent, mvoltage,ttime, external_value))
                
                i += 1
                
                self.time.append(datetime.datetime.now())
                self.intensity.append(mcurrent)
                self.voltage.append(mvoltage)
                    
                        
                if self.value != value:
                    value = self.value
                    
                    if self.mode == 'CC':
                          self.keithley.mode_ifix_setcurr(self.value / 1000.0,curr_max=0.1, curr_min= 0.00)
                    else:
                          self.keithley.mode_vfix_setvolt(self.value )
                                
                if dt_fix:
                    sleeping_time = dt
                else:
                    sleeping_time = dt_calc(etime)
                        
                while (monotonic() - time1) < sleeping_time and self.running:
                    sleep(0.01)
                    
            except KeyboardInterrupt:
                # In case of error turn off the source anyway and stop the program
                print('INFO: Programm interrupted in a safe way\n')
                break
            
            except Exception as e:
                # In case of ANY error turn off the source anyway and stop the program while printing the error
                print(e)
                self.keithley.outpoff()
                break
    
        if interrupt_measurement:
            print('INFO: Measurement stopped, but sourcemeter still on\n') 
        else:
            self.keithley.outpoff()                
              
    def measurement_on(self):
        self.running = True
      
    def measurement_off(self):
        self.running = False