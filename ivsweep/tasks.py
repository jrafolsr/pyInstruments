# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 10:37:57 2020

@author: OPEGLAB
"""


# coding: utf-8
# Library that depends on the pyLab library and that contains the main program/functions
# for driving the LEC devices at diferent modes.

import numpy as np
from pyInstruments.instruments import keithley24XX # This the module I created
import datetime
from pathlib import Path
 
class IVSweeperTask(object):
    def __init__(self, resource = None, folder = '.\\', filename = 'voltsge-sweep',\
                  start = 0, stop = 1, step = 0.1, mode = 'step', sweep_list = [],\
                  term = 'FRONT', cmpl = 0.1, delay = 0.1, ranging = 'AUTO', nplc = 1, spacing = 'LIN'):
        """
        Parameters
        ----------
        resource : str, optional
            The resource name for the sourcemeter Keithley24XX, default is 'GPIB0::24::INSTR'. The default is 'GPIB0::24::INSTR'.
        folder : str, optional
            Folder where to save the data, abs o relative. The default is '.\'.
        filename : bool, optional
            Filename where to save the data. Always append if the file already exists. The default is 'voltage-time-data'.
        start: int ot float
            Initial voltage in V in case of a stair-like sweep.
        stop: int ot float
            Final voltage in V in case of a stair-like sweep.           
        step: int ot float
            Voltage step in V in case of a stair-like sweep.
        mode: 'step' or 'list'
            Sweep mode. If 'step' the values start, stop, step and spacing are used to configure the sweep-list values. If 'list' the list passed to the 'sweep_list' argument will be used. The default is 'step'.
        term: 'FRONT' ot 'REAR'
            The output terminal to use. the default is 'FRONT'
        cmpl: itn or float
            The compliance value in A.
        nplc: int or float 0.01 <= nplc <=100
            Numebr of pulse light cycles to average the data. The default is 1.
       ranging: 'AUTO' or float
           Set the current sensign range to a fix one in the case a value is passed. The default is None and the sourcemeter will adjust the range according to the measured values.
       spacing:'LIN'  or 'LOG'
          Spacing type of the values in the case of a stair-like sweep.
       delay: int or float
           Specify delay in seconds between the settled source value and the measurement reading. 
        Returns
        -------
        None.

        """

        self.max_length = 500
        self.time = []
        self.voltage = []
        self.intensity = []
        self.resource = resource
        self.folder = Path(folder)
        self.filename = filename

        self.configuration = dict(start = start, stop = stop, step = step, mode = mode, sweep_list = sweep_list,\
                                  term = term, cmpl = cmpl, delay = delay, ranging = ranging, nplc = nplc, spacing = spacing)
        self.data_ready = False
        
    def start_instrument(self):
        """
        Powers on the instrument.
        
        """
        
        # Opening the resource only done if not done before
        if self.resource is  None:
            raise ValueError('The sourcemeter resource has not been defined. Please define it throught the resource attribute')
            
        self.keithley = keithley24XX(self.resource)
        self.keithley.mode_Vsweep_config(**self.configuration)
            
    def run(self):
        """
        Engages the sweep.
        """
        
        ############  LOGGING THE DATA ###################################
        # Opening the file to save the data
        filename = Path(self.folder) / (self.filename + '.txt')  
        
        if not filename.exists():
            with open(filename,'a') as f:
                f.write(('# ' + 3*'{:^12}\t' + '\n').format('Voltage(V)','Current(A)', 'Time(s)'))
        

        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")
        
        data = self.keithley.sweep_read()
        
        with open(filename,'a') as f:
            f.write('# {}\n'.format(timestamp))
            f.write('# Delay between steps: {}\n'.format(self.configuration['delay']))
            np.savetxt(f, data[:,[0,1,3]], fmt = '%.6f')
        
        self.voltage = data[:,0]
        self.intensity = data[:,1]
        self.time = data[:,3]
        self.data_ready = True