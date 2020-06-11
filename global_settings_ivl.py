# -*- coding: utf-8 -*-
"""
Created on Fri Oct 25 12:28:38 2019

@author: OPEGLAB
"""
from collections import deque
global VOLTAGE, CURRENT, CONFIG_STATUS, MEASUREMENT_ON, LUMINANCE,\
 CONFIGURATION, SET_CURRENT, MAX_LENGTH

from numpy import inf
def init():
    global VOLTAGE, CURRENT, CONFIG_STATUS, MEASUREMENT_ON, LUMINANCE, ETIME,\
    CONFIGURATION,  SET_CURRENT, MAX_LENGTH
    MAX_LENGTH = 500
    ETIME = deque([], MAX_LENGTH)
    LUMINANCE = deque([], MAX_LENGTH)
    VOLTAGE = deque([], MAX_LENGTH)
    CURRENT =  deque([], MAX_LENGTH)
    SET_CURRENT = 0.0
    CONFIG_STATUS = True
    MEASUREMENT_ON = False

    CONFIGURATION = {'current' : 0.00,
              'rtime' : inf,
              'dt' : 0.25,
              'folder' : '.\\',
              'fname' : 'voltage-time-data',
              'resource1' : 'GPIB0::24::INSTR',
              'term' : 'FRONT',
              'fw' : False,
              'beeper' : True,
              'cmpl' : 21.0,
              'Ncount' : 1,
              'aver' : False,
              'nplc' : 1.0,
              'config' : CONFIG_STATUS,
              'interrupt_measurement' : False,
              'dt_fix' : False,
              'device' : 'Dev1',
              'adqTime' : 0.05,
              'adqFreq' : 10000,
              'list_channels'  : [1],
              'rang_channels' : [10],
              'mode' : 'FiniteSamps',
              'terminalConfig' : 'SE'}

def get_configuration():
    global CONFIGURATION
    return (value for value in CONFIGURATION.values())

def set_configuration(key, value):
    global CONFIGURATION
    CONFIGURATION[key] = value