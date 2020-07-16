# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 10:18:00 2019

@author: OPEGLAB
"""
global CURRENT_T, SETPOINT_T, CURRENT_ACTION, CURRENT_I, CURRENT_V,\
    PID_STATUS, PID_ON, MAX_A, MIN_A

def init():
    global CURRENT_T, SETPOINT_T, CURRENT_ACTION, CURRENT_I, CURRENT_V,\
    PID_STATUS, PID_ON, MAX_A, MIN_A
    CURRENT_T = 20.0
    SETPOINT_T = 20.0
    CURRENT_ACTION = 0.0
    CURRENT_I = 0.0
    CURRENT_V = 0.0
    PID_STATUS = True
    PID_ON = False
    MAX_A = 15.0
    MIN_A = 0.0
    
    
