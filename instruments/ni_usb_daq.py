# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 16:40:13 2019

@author: JOANRR
"""
# The following are for the DAQ class only
import numpy as np
from ctypes import *
# Uncomment the following  3 lines if you want to use the DAQ libraries 
from PyDAQmx import Task, int32, DAQmx_Val_Volts, DAQmx_Val_Diff,\
  DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, DAQmx_Val_ContSamps,\
  DAQmx_Val_GroupByChannel, DAQmx_Val_RSE, DAQmx_Val_RisingSlope




class daq(object):
    """This class prepares and configures a DAQ system for an analog adquisition. The required
    arguments are the name of the device as a string (p.e. 'Dev3'), the adquisition time in seconds
    (adqTime), the sampling frequency in Hz (adqFreq), the channels to read as a list of integer values
    with the available channels, the voltage range of the channels as a list with the maximum positive
    voltage value and with the same length as the channel list.
    
    Optional arguments:
        - mode = 'FiniteSamps': sets the adquisiton mode to finite sampling (default) or continuous 'ContSamps'
        - trigger = None: sets the trigger mode. If None it is taken as the clock edge. Otherwise,
                    a 2-element list can be passed, the first value being the channel number and the second
                    the voltage value to configure the trigger to an analog channel in rising mode.
    
    This class only contemplates reading volts signal of analog inputs in differential configuration.
    Future versions might implement other possibilities."""
    def __init__(self, device, adqTime, adqFreq, list_channels, rang_channels, mode = 'FiniteSamps', trigger = None, terminalConfig='diff'):
        """This will configure the DAQ and Task for the specified configuration"""
        self.device = device
        self.adqTime = adqTime # In seconds
        self.adqFreq = adqFreq
        self.list_channels = list_channels
        self.rang_channels = rang_channels
        self.mode = mode
        self.N_samples = int(adqTime * adqFreq)
        self.N_channels = len(list_channels)
        if terminalConfig is 'diff':
            self.terminalConfig = DAQmx_Val_Diff
        elif terminalConfig is 'SE':
            self.terminalConfig = DAQmx_Val_RSE
        else:
            raise Error('Terminal configuration "{}" not known'.format(terminalConfig))
        print('I will adquire {} samples for each {} channels'.format(self.N_samples, self.N_channels))
        # DAQmx Configure Code
        # We create a Task instance
        self.ai = Task()
        # Prepare the type of variable that it returns using the library ctypes that work with C-functions
        self.read = int32()
        # The vector data will contain the output of the DAQ card in a single vector with the data from different channels
        # in a single 1-D vector with the data concatenated
        self.data = np.zeros((self.N_samples * self.N_channels,), dtype = np.float64)
        #self.ai = Task()
        # This prepares the string that is needed for the ``CreateAIVoltageChan`` depending on the number of channels to
        # read
        for channel, Vrange in zip(self.list_channels,self.rang_channels):
            str_channels = r"{}/ai{:d}".format(self.device,channel)  
            #print(r"{}/ai{:d}".format(self.device,channel) )
            self.ai.CreateAIVoltageChan(str_channels,"",self.terminalConfig,-1.0*Vrange,Vrange, DAQmx_Val_Volts,None)

        if mode is 'FiniteSamps':
            self.ai.CfgSampClkTiming("",self.adqFreq,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,self.N_samples)
        elif mode is 'ContSamps':
            self.ai.CfgSampClkTiming("",self.adqFreq,DAQmx_Val_Rising,DAQmx_Val_ContSamps,self.N_samples)
        else:
            raise Error('Mode not known')
        if trigger is None:
            pass
        else:
            self.ai.CfgAnlgEdgeStartTrig(r"{}/ai{:d}".format(self.device,trigger[0]) ,DAQmx_Val_RisingSlope,trigger[1])
        # In the case the DAQ accept a trigger from one of the analog channels we could also setup it as
        # 
    def start(self):
        self.ai.StartTask()
    def stop(self):
        self.ai.StopTask()
        self.data = np.zeros((self.N_samples * self.N_channels,), dtype = np.float64)
    def read_analog(self, timeout = 10.0):
        """Calls the ReadAnalogF64 with the configured parameters.
        
        Optional arguments:
            - timeout = 10.0: timeout in number of seconds.
        """
        self.ai.ReadAnalogF64(self.N_samples, timeout,DAQmx_Val_GroupByChannel, self.data,self.N_samples * self.N_channels, byref(self.read), None)
        return self.data.reshape((self.N_samples,self.N_channels), order = "F")
    def clear(self):
        self.ai.ClearTask()