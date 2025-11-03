# -*- coding: utf-8 -*-
"""
Created on Fri Sep 30 08:46:18 2022

@author: JOANRR
"""
from time import sleep, monotonic
from numpy import inf

class Timer(object):   
    def __init__(self, max_time = inf, min_time_step = 0.5, max_time_step = 30, fix_step = True, intervals = (5, 60, 300, 3600)):
        """
        Timer object to time the long measurements with and adaptative (or not) time step.
        
        Parameters
        ----------
        max_time :  float, optional
            Maximum time to run the timer in seconds.
        min_time_step : float, optional
            Minimum time interval allowed in seconds.
        max_time_step : float, optional
            Maximum time interval allowed in seconds.
        fix_step : bool, optional
            Wether to use or not a fix time interval. The default is False. 
            
        Returns
        -------
        None.
        """
        # Initialize last_measured time to 0.0
        self.last_measured_time = 0.0
        self.max_time = max_time
        self.min_time_step = min_time_step
        self.max_time_step = max_time_step
        self.time_step = min_time_step
        self.fix_step = fix_step
        self.initialized = False
        self.counter = 0
        self.intervals = intervals
        
    def initialize(self):
        """
        Initializes the timer, not to be confused with the __init__() to initialized the object.

        """
        self.time0 = monotonic()
        self.last_measured_time = 0.0
        self.initialized = True
        self.timer_active = True
        self.counter += 1
    
    def reset_counter(self):
        self.counter = 0
        
    def ellapsed_time(self):
        """
        Calculates the ellapsed time using the monotonic function from time library.
        """
        if not self.initialized:
            self.initialize()
        return monotonic() - self.time0
    
    def expired(self):
        """
        Returns a booled whether the timer has expired (True) or not (False), depending on whether the max_time has been surpassed
        """
        
        if not self.initialized:
            return False
        
        if monotonic() - self.time0  < self.max_time:
            return False
        else:
            return True
        
    def istime2measure(self):
        """
        Condition to whether to save at timestamp/measurement or not.
        """
        # Update the time step only if the fix_time is False
        if not self.fix_step: self.update_time_step()
        
        if self.ellapsed_time() >= self.last_measured_time + self.time_step:
            # Record the last timestamp, assume that I am going to do the measurement
            self.last_measured_time = self.ellapsed_time()
            return True
        else:
            return False
        
    def update_time_step(self):
        """
        Changes the timestep based on the total ellapsed time.
        """
        etime  = self.ellapsed_time()
        if etime <= self.intervals[0]:
            self.time_step = self.min_time_step
        elif etime <= self.intervals[1]:
            self.time_step =  min(2 * self.min_time_step, self.max_time_step)
        elif etime <= self.intervals[2]:
            self.time_step =  min(5 * self.min_time_step, self.max_time_step)
        elif etime <= self.intervals[3]:
            self.time_step =  min(10 * self.min_time_step, self.max_time_step)
        else:
            self.time_step = self.max_time_step



if __name__ == '__main__':
    # Testing the Timer
    myTimer = Timer(fix_step=False)
    
    
    x = 1
    i = 0
    k = 0
    filename = 'test_timer.log'
    with open(filename, 'w') as f:
        f.write('# Step\tSavedStep\tTime(s)\n')
    
    while True:
        try:
            # x += x
            i += 1
            
            etime = myTimer.ellapsed_time()
            fmeasure = myTimer.istime2measure()
            tstep = myTimer.time_step
            
            if fmeasure:
                k += 1
                s = f'{i:04d}\t{k:04d}\t{etime: 6.4f}\t{tstep: 6.4f}\n'
                print(s[:-2])
                with open(filename, 'a') as f:
                    f.write(s)
            
            sleep(0.0001)
            # x = 1 if x > 1e4 else x
        except KeyboardInterrupt:
            break
    
