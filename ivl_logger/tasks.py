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
from collections import deque
from pyGonioSpectrometer.instrumentation import SpectraMeasurement, list_spectrometers
from pyvisa import ResourceManager
from threading import Thread

def dt_calc(etime):
    """Returns an interval of time that increased as the ellapsed time etime increases"""
    if etime <= 60:
        return 5
    elif etime <= 300:
        return 10
    elif etime <= 600:
        return 30
    elif etime <= 3600:
        return 60
    else:
        return 300
 
class IVL_LoggerTask(object):
    def __init__(self, sourcemeter = None, spectrometer = None, integration_time = 100, n_spectra = 1, folder = '.\\', filename = 'voltage-spectra-time-data',\
                  mode = 'CC', term = 'FRONT', fw = False, beeper = True, cmpl = 21.0, Ncount = 1,\
                  aver = False, nplc = 1.0, config_flag = True):
        """
        Parameters
        ----------
        sourcemeter : str, optional
            The resource name for the sourcemeter Keithley24XXThe default is None.
        spectrometer :  seabreeze.spectrometers.Spectrometer class, optional
            The resource name for the spectrometer. The default is None.
        integration_time : int or float, optional
            Sets the integration time in ms. The default is 100.   
        n_spectra : int, optional 
            Number of spectra that will be averaged when using the method get_averaged_spectra(). The default is 1.               
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
        self.sourcemeter = sourcemeter
        self.spectrometer = spectrometer
        self.folder = folder
        self.filename = filename
        self.mode = mode
        self.configuration = dict(term = term, fw = fw, beeper = beeper, cmpl = cmpl, Ncount = Ncount, aver = aver, nplc = nplc)
        self.configuration_spectrometer = dict(integration_time = integration_time, n_spectra = n_spectra)
        
        self.config_flag = config_flag
        self.value = 0.00
        self.min_counts_allowed = 10000
        
        
    def configurate(self):
        """
        Configurates and powers the instrument on the instrument.
        
        """
        
        # Opening the sourcemeter only done if not done before
        if self.sourcemeter == None:
            raise ValueError('The sourcemeter resource has not been defined. Please define it throught the sourcemeter attribute')
            
        self.keithley = keithley24XX(self.sourcemeter)

        if self.config_flag:
            if self.mode == 'CC':
                print('INFO: Instrument configured in CC mode.')
                self.keithley.mode_ifix_configure(**self.configuration)
            elif self.mode == 'CV':
                print('INFO: Instrument configured in CV mode.')
                self.keithley.mode_vfix_configure(**self.configuration)
            else:
                raise ValueError('ERROR: Configuration mode not known! Only CC or CV allowed')
                
        # Opening the spectrometer only done if not done before
        if self.spectrometer == None:
            raise ValueError('The spectrometer resource has not been defined. Please define it throught the spectrometer attribute')
        
        self.flame = SpectraMeasurement(self.spectrometer, **self.configuration_spectrometer)
        self.wavelengths = self.flame.get_wavelengths()
                
            
    def run(self, value, runtime = np.inf):
        """
        Parameters
        ----------
        value : float
            Current (in mA) or voltage (V) setpoint value.
        runtime : float, optional
            Running time of the experiment in seconds. The default is np.inf.
        dt : float, optional
            Rime inverval between measurements. The default is 0.25.
        dt_fix : bool, optional
            If True, the time interval is fixed. If set to False, then it uses the time interval from the function dt_calc(). The default is True.

        """
        
        ############  LOGGING THE DATA ###################################
        # Opening the file to save the data
        self.filename = os.path.join(self.folder, self.filename + f'_{self.flame.integration_time/1000:.0f}ms.txt')
        
        if not os.path.isfile(self.filename):
            with open(self.filename,'a') as f:
                f.write(('# '+ 5*'{:^12}\t' + '\n').format('EllapsedTime','Current','Voltage', 'Integration Time', 'Spectra'))
                f.write(('# '+ 5*'{:^12}\t' + '\n').format('s','mA', 'V', 'ms','counts'))
        
        # Saving the wavelength vector
        self.write2file(np.nan, np.nan, np.nan, np.nan, self.wavelengths)
        
        # Taking and saving the dark spectra
        tspectra = self.flame.get_averaged_intensities()
        # Saving the wavelength vector
        self.write2file(np.nan, np.nan, np.nan, self.flame.integration_time / 1000, tspectra)
        print('Current value: ', value)
        if self.mode == 'CC':
              self.keithley.mode_ifix_setcurr(value / 1000.0, curr_max = 0.1, curr_min= 0.00)
        else:
              self.keithley.mode_vfix_setvolt(value)
        
        ttime = 0.0
        etime= 0.0 # Ellapsed time
        itime = time() # Initial time
        i = 0 # Step counter
        
        print('# Measurement started')
        self.keithley.outpon()
        self.running = True

        while etime < runtime and self.running:
            try:
                time1 = time()
                
                [mvoltage, mcurrent, _ , ttime, _ ] =   self.keithley.read()
                tspectra = self.flame.get_averaged_intensities()
    
                etime = time() - itime 
                
                self.write2file(etime, mcurrent*1000.0, mvoltage, self.flame.integration_time / 1000, tspectra)
                
                print(f'\r #{i+1:2d}, ellapsed time = {etime:.1f} s, V = {mvoltage:.2f} V, I = {mcurrent*1000:.2f} mA', end = '')
                
                # Check for any values higher than saturation
                if np.any(tspectra > self.flame.saturation_counts):
                    print('\n! WARNING: Some values are saturating. Consider lowering the integration time.')
                elif tspectra.max() < self.min_counts_allowed:
                    print('\n! WARNING: The max. count is less than 10000. Consider increasing the integration time')
                
                
                i += 1
                
                self.time.append(datetime.datetime.now())
                self.intensity.append(mcurrent)
                self.voltage.append(mvoltage)
                self.spectra = tspectra
                        
                if self.value != value:
                    value = self.value
                    
                    if self.mode == 'CC':
                          self.keithley.mode_ifix_setcurr(self.value / 1000.0,curr_max=0.1, curr_min= 0.00)
                    else:
                          self.keithley.mode_vfix_setvolt(self.value)
                                

                sleeping_time = dt_calc(etime)
                        
                while ((time() - time1) < sleeping_time) & self.running:
                    sleep(0.01)
                    
            except KeyboardInterrupt:
                # In case of error turn off the source anyway and stop the program
                print('INFO: Programm interrupted in a safe way\n')
                break
            
            except Exception as e:
                # In case of ANY error turn off the source anyway and stop the program while printing the error
                print(e)
                break
    
        self.keithley.outpoff()                
        self.flame.close()
        
    def measurement_on(self):
        self.running = True
      
    def measurement_off(self):
        self.running = False
        
    def write2file(self, etime, current, voltage, integration_time, data):
        """
        Write to a file
        """
        t  = np.hstack((etime, current, voltage, integration_time, data))
        t = t.reshape((1, t.shape[0]))
        with open(self.filename, 'a') as f:
           np.savetxt(f, t, fmt = '% 8.2f')

if __name__ == '__main__':
        # This will only be used if the script is called as it is, not if it is used as a function
    # Assume the first port is the Arduino
    lspectrometers = list_spectrometers()
    spectrometer  = None if len(lspectrometers) == 0 else lspectrometers[0]
    print(f'Spectrometer: {spectrometer}')
    
    # Assuming there is only one spectrometer, so taking the first element
    list_of_resources = ResourceManager().list_resources()
    default_resource = [s for s in list_of_resources if 'GPIB' in s]
    sourcemeter = None if len(default_resource) == 0 else default_resource[0]
    
    print(f'Sourcemeter: {sourcemeter}')
    
    integration_time =200
    
    n_spectra = 1
    
    folder = r'C:\Users\JOANRR\Documents\Python Scripts\data\Etienne'
    
    filename = 'test02'
    
    m = IVL_LoggerTask(sourcemeter=sourcemeter, spectrometer=spectrometer, integration_time=integration_time, n_spectra=n_spectra, folder = folder, filename = filename)
    
    intensity = 1.0 #mA
    
    m.configuration['term'] = 'FRONT'
    m.value = intensity
    m.configurate()
    
    print('Press Ctrl+C to interrupt the measurement')
    
    thread = Thread(target = m.run, args = (intensity, ))
    thread.daemon = True
    thread.start()
    