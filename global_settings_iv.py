# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 12:28:38 2019

@author: OPEGLAB
"""
from collections import deque
global VOLTAGE, CURRENT, CONFIG_STATUS, MEASUREMENT_ON,\
 CONFIGURATION, SET_CURRENT,SET_VALUE, MAX_LENGTH, MODE

from numpy import inf

def init():
    global VOLTAGE, CURRENT, CONFIG_STATUS, MEASUREMENT_ON, ETIME,\
    CONFIGURATION,  SET_CURRENT,SET_VALUE, MAX_LENGTH, MODE
    
    MAX_LENGTH = 500
    ETIME = deque([], MAX_LENGTH)
    VOLTAGE = deque([], MAX_LENGTH)
    CURRENT =  deque([], MAX_LENGTH)
    SET_CURRENT = 0.0
    SET_VALUE = 0.0
    CONFIG_STATUS = True
    MEASUREMENT_ON = False
    MODE = 'CC'
    
    CONFIGURATION = {
              'mode' : MODE,
              'rtime' : inf,
              'dt' : 0.25,
              'folder' : '.\\',
              'fname' : 'voltage-time-data',
              'resource1' : 'GPIB0::24::INSTR',
              'term' : 'REAR',
              'fw' : False,
              'beeper' : True,
              'cmpl' : 21.0,
              'Ncount' : 1,
              'aver' : False,
              'nplc' : 1.0,
              'config' : CONFIG_STATUS,
              'interrupt_measurement' : False,
              'dt_fix' : False
              }

def get_configuration():
    global CONFIGURATION, SET_VALUE
    args = tuple([SET_VALUE])
    kwargs = CONFIGURATION
    return args, kwargs

def set_configuration(key, value):
    global CONFIGURATION
    CONFIGURATION[key] = value