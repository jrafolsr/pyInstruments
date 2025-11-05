# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 16:42:41 2019

@author: JOANRR
"""
from time import monotonic

class Pid(object):
    
    def __init__(self, Kp, Ki, Kd, ulimit = 0.020, llimit = 3.5e-5):
        """Initalize all values for the PID"""
        # Values of the pid
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.ti = 0.0
        self.td = 0.0
        self.dt = 0.0
        # Check for the first call
        self.first_call  = True
        # Setpoint and value
        self.setpoint = 0.0
        self.value = 0.0
        # Limits of the action provided by the user
        self.set_ulimit(ulimit)
        self.set_llimit(llimit)
    def set_ulimit(self, limit):
        """This method sets the maximum value of the action of PID"""
        self.ulimit = limit
        print("The action maximum value will be limited  to {:.2g}".format(self.ulimit))
    def set_llimit(self, limit):
        """This method sets the minimum value of the action of PID"""
        self.llimit = limit
        print("The action minimum value will be limited to {:.2g}".format(self.llimit))
    def set_setpoint(self,setpoint):
        """This method sets the setpoint value of the PID"""
        self.setpoint = setpoint
    def update(self, value, setpoint = None):
        """This function updates the value of the action. It needs the reference current value of the control\
        variable. It No setpoint is provided, the setpoint is taken from the attribute self.setpoint"""
        if setpoint is not None:
            self.setpoint = setpoint
        if self.first_call:
            self.prev_time = monotonic()
            self.first_call = False
        # Update all the values
        self.dt = monotonic() - self.prev_time
        self.value = value
        error = self.setpoint - self.value
        pi = self.Kp * error
        ti = self.Ki * error * self.dt
        
        if self.dt > 0:
            td = self.Kd * error  / self.dt
        else:
            td = 0
        
        action = pi + (self.ti + ti) + td - self.td

        print('\n\n\n-----------------------ACTION ---------------')
        print(f'action BEFORE {action:.4f}')
        if self.llimit < action < self.ulimit:
            self.ti = self.ti + ti
            self.td = td -self.td
        elif action > self.ulimit:
            print(f'OBS! The action {action:.4f} > upper limit {self.ulimit:.4f}')
            action = self.ulimit
        else:
            print(f'OBS! The action {action:.4f} < lower limit {self.llimit:.4f}')
            action = self.llimit
        
        print('------------------------ACTION ---------------')
        print(f'action AFTER {action:.4f}\n\n\n')
        
        
        self.prev_time = monotonic()

        return action
    def clear(self):
        """Clears and resets the PID to the initial values of the integrative and derivative factors"""
        self.ti = 0.0
        self.td = 0.0
        self.dt = 0.0
        self.first_call = True
