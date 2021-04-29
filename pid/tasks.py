# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 11:24:33 2018

@author: joan-fss
"""
#%%
from time import sleep, time
from pyInstruments.instruments import keysight34461A, agilentE36XXA # This the module I created
from pyInstruments.pid import Pid
import datetime
from numpy import sqrt, isclose, nan
from threading  import Lock
today = datetime.date.today().strftime("%d%m%Y")
from pathlib import Path

def calc_temperature(R, R0 = 100.0, alpha = 3.9083e-3, beta =  -5.7750e-7):
    """Returns the temperature in °C according to the Standard Class B Pt100/1000, default is Pt100"""

    return (-alpha + sqrt(alpha**2-4 * beta * (1-R / R0))) / 2 / beta


#%%

class TemperatureController(object):
    def __init__(self):
        """
        Initializes the pid.

        """
        # Initialize some variables
        self.setpoint = nan
        self.current_T = nan
        # Creates a lock class to block the access to the temperature writing
        self.lock = Lock()
        # Files to store and read the setpoint and Treal
        self.log_file = Path('../temp/temp.dat')
        
        
    
    def configurate(self, setpoint = 20.0, heating = True, max_poutput = 12.00,\
                   multimeter_addr  = 'GPIB0::23::INSTR',\
                   sourcemeter_addr = 'GPIB0::5::INSTR',\
                   R0 = 100 ):
        """
        Configures the pid

        Parameters
        ----------
        setpoint : float, optional
            Setpoint in °C. The default is 20.0.
        heating : bool, optional
            Whether to heat or to cool, important for the Peltier polarity and pid action calculation. The default is True.
        max_poutput : float, optional
            Max. action allowed from the pid, in this case, in Volts. The default is 12.
        multimeter_addr : str, optional
            Adress of the multimeter, which reads the temperature. The default is 'GPIB0::23::INSTR'.
        sourcemeter_addr : TYPE, optional
            Adress of the power supply, which powers the heating/cooling element. The default is 'GPIB0::5::INSTR'.
        R0 : int, optional
            The R0 pf the RTD sensor used, typically either 100 or 1000. The default is 100.

        Returns
        -------
        None.
        
        """  
        # Initialize the properties of the class
        self.setpoint = setpoint
        self.heating = heating
        self.pid_running = False
        self.max_poutput = max_poutput
        self.R0 = R0
        
        # Configuration of the sourcemeter and measurement devices
        self.mult = keysight34461A(multimeter_addr)
        self.supply  = agilentE36XXA(sourcemeter_addr)
        
        if R0 == 100:
            # Range to read a Pt100
            self.mult.config_ohms(rang = 1000, nplc = 1, count = 5)      
        else:
            # Range to read a Pt1000
            self.mult.config_ohms(rang = 10000, nplc = 1, count = 5)   
                
        terminal = 'default'
        if heating:
    #    terminal = 'P25V'
            self.pmin = 0.0
            self.pmax = self.max_poutput
        else:
    #        terminal = 'N25V'
            self.pmin = -1.0 * self.max_poutput
            self.pmax = 0.0
        
        self.supply.config_volt(0.0, output = terminal)
        
    def run(self, sleeping_time = 0.5):
        """
        Starts the temperature control.
        
        Parameters
        ----------
        sleeping_time : float, optional
            Time interval in which teh pid algorithm is fed. The default is 0.5.

        Returns
        -------
        None.

        """
        # PID setup (parameters for Peltier and working well and tested for dt = 0.25 to 1 s)
        Kp = 1.0 
        Ki = 0.05
        Kd = 0.0
    
        pid = Pid(Kp,Ki,Kd, ulimit = self.pmax, llimit = self.pmin)
        
        pid.clear() # Not really necessary now, but it is a good practice. It resets all the values of the pid.
    
        # Read and write the current temperature
        self.current_T = calc_temperature(self.mult.read(), self.R0).mean(axis = 0)
        
        pid.set_setpoint(self.current_T) # Initialize the setpoint to a the current temperature
              
        while self.pid_running:
            try:
                time1 = time()
                
                # Turn the Power supply on OBS! i CAN DELETED THAT ONE, i THINK, DOUBLE CHECK
                if not self.supply.outpstate():
                    print('INFO: Turning on the Power supply')
                    self.supply.outpon()
                 
                if self.heating:
                    pid.ulimit = self.max_poutput
                else:
                    pid.llimit = -1.0 * self.max_poutput
                
                T  = calc_temperature(self.mult.read(), self.R0).mean(axis = 0)

                # Update the action value to steadily reach the setpoint based on how close is from the final value                       
                if self.heating:
                    if isclose(T, self.setpoint, 0, 0.5) or (T >= self.setpoint + 0.5):
                        # If it is already close to the final setpoint, no need to do the ramp
                        action = pid.update(T, self.setpoint)
                    else:
                        # If it is far from the final setpoint, increase steadily theat 20 °C/min
                        action = pid.update(T, pid.setpoint + 20.0/60.0 * pid.dt)
                else:
                    if isclose(T, self.setpoint, 0, 0.5) or (T <= self.setpoint - 0.5):
                        action = pid.update(T, self.setpoint)
                    else:
                        action = pid.update(T, pid.setpoint - 20/60.0*pid.dt)

                action = abs(action)
                self.supply.set_volt(action)    
                
                self.current_T = T
                self.current_action = action
                self.current_voltage = action
                self.current_intensity = self.supply.read_value(value = 'curr')
                
                with self.lock:
                    with open(self.log_file, 'w') as f:
                        f.write(f'{T:5.2f}')
                
                # Check the pid status
                while (time() - time1) < sleeping_time:
                    sleep(0.01)
                
            except KeyboardInterrupt:
                print('INFO: Pid program interrupted in a safe way\n')
                break
            
            except Exception as e:
                # In case of ANY error turn off the source anyway and stop the program while printing the error
                print(e)
                break
        
        pid.clear()
        self.supply.set_volt(0.0)
        self.supply.outpoff()
        
        return None

    def pid_on(self):
        """
        Sets the pid to the on status.
        
        """
        self.pid_running = True

    def pid_off(self):
        """
        Sets the pid to the off status.
        
        """
        self.pid_running = False
        
        with self.lock:
            with open(self.log_file,'w') as f:
                f.write('nan') 
        
        
       
    def set_setpoint(self, value, min_value = -20, max_value = 100):
        """
        Re-sets the setpoint of the pid task, considering the min and max value.

        Parameters
        ----------
        value : float
            Setpoint in Celsius degrees.
        min_value : TYPE, optional
            Min value of the temperature allowed in °C. The default is -20.
        max_value : TYPE, optional
            Max value of the temperature allowed in °C. The default is 100.

        """

        if value > max_value:
            value = max_value
            print(f'INFO: Temperature beyong the established limits of {min_value:.2f} and {max_value:.2f} °C\n')
        elif value < min_value:
            value = min_value
            print(f'INFO: Temperature beyong the established limits of {min_value:.2f} and {max_value:.2f} °C\n')    
        
        self.setpoint= value 


if __name__ == '__main__':
    print('Functions for the pid loaded \n')