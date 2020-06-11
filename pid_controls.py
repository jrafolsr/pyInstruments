# -*- coding: utf-8 -*-
"""
Created on Thu Oct  4 11:24:33 2018

@author: joan-fss
"""
#%%
from time import sleep, time
from pyLab_v2.instruments import keysight34461A, agilentE3631A # This the module I created
import pyLab_v2.pid as pid_object
import pyLab_v2.global_settings_pid as gs

import datetime
from numpy import sqrt, isclose
from threading  import Thread, Lock
today = datetime.date.today().strftime("%d%m%Y")




def calc_temperature(R, cal = {'R0' : 100.0, 'alpha' : 3.9083e-3, 'beta' : -5.7750e-7}):
    """Returns the temperature in °C according to the Standard Class B Pt100/1000, default is Pt100"""
    return (-cal['alpha'] + sqrt(cal['alpha']**2-4*cal['beta']*(1-R/cal['R0'])))/2/cal['beta']

# Creates a lock class to block the access to the temperature writing
# Files to store and read the setpoint and Treal
fTreal = r'.\temp\temp.dat'
lock = Lock()
#%%
def pid_controller(setpoint = 20.0, heating = True, max_poutput = 12.00):
    gs.SETPOINT_T = setpoint
    gs.MODE_HEATING = heating
    gs.MAX_A = max_poutput
    # Creating the object class ktly20XX
    mult = keysight34461A('GPIB0::23::INSTR')
    supply  = agilentE3631A('GPIB0::5::INSTR')
    # Configuration of the sourcemeter and measurement devices
    mult.config_ohms(rang = 1000, nplc = 1, count = 5)
    
    if gs.MODE_HEATING:
        terminal = 'P25V'
        pmin = 0.0
        pmax = gs.MAX_A
    else:
        terminal = 'N25V'
        pmin = gs.MAX_A*(-1.0)
        pmax = 0.0
    
    supply.config_volt(0.0, output = terminal)
    
#    supply.outpon()
    # PID setup (parameters for Peltier and working well and tested for dt = 0.25 to 1 s)
    Kp = 1.0 
    Ki = 0.05
    Kd = 0.0

    pid = pid_object(Kp,Ki,Kd, ulimit = pmax, llimit = pmin)
    pid.clear() # Not really necessary now, but it is a good practice. It resets all the values of the pid.

    # Read and write the current temperature
    gs.CURRENT_T = calc_temperature(mult.read()).mean(axis = 0)
    pid.set_setpoint(gs.CURRENT_T) # initialize the setpoint to a the current temperature
    
    sleeping_time = 0.5
    
    while gs.PID_STATUS:
        try:
            time1 = time()
            if gs.PID_ON:
                # Turn the Power supply on
                if not supply.outpstate():
                    print('Turning on the Power supply')
                    supply.outpon()
                if gs.MODE_HEATING:
                    pid.ulimit = gs.MAX_A
                else:
                    pid.llimit = gs.MAX_A*(-1.0)
                
                T  = calc_temperature(mult.read()).mean(axis = 0)
                    
                # Update the action value to steadily reach the setpoint based on how close is from the final value                       
                if gs.MODE_HEATING:
                    if isclose(T,gs.SETPOINT_T,0,0.5) or (T >= gs.SETPOINT_T + 0.5):
                        action = pid.update(T, gs.SETPOINT_T)
                    else:
                        action = pid.update(T, pid.setpoint + 20/60.0*pid.dt)
                else:
                    if isclose(T,gs.SETPOINT_T,0,0.5) or (T <= gs.SETPOINT_T - 0.5):
                        action = pid.update(T, gs.SETPOINT_T)
                    else:
                        action = pid.update(T, pid.setpoint - 20/60.0*pid.dt)
                
                supply.set_volt(action)    
                
                gs.CURRENT_T = T
                gs.CURRENT_ACTION = action
                gs.CURRENT_V = action
                gs.CURRENT_I = supply.read_value(value = 'curr')
                
                with lock:
                    with open(fTreal,'w') as f:
                        f.write(f'{T:5.2f}')
            else:
                pid.clear()
                supply.set_volt(0.0)
                supply.outpoff()
                
                # Check the pid status
            while (time() - time1) < sleeping_time:
                sleep(0.01)
            
        except KeyboardInterrupt:
            # In case of error turn off the source anyway and stop the program
            print('Programm interrupted in a safe way\n')
            break
        except Exception as e:
            # In case of ANY error turn off the source anyway and stop the program while printing the error
            print(e)
            break
    
    supply.outpoff()
    mult.outpoff()
    return None

def pid_on():
    gs.PID_STATUS = True
def pid_off():
    gs.PID_STATUS = False
def pid_start():
    gs.PID_ON = True
def pid_stop():
    gs.PID_ON = False
def pid_setpoint(value):
    llim = -20
    hlim = 100
    if value > hlim:
        value = hlim
        print(f'Temperature beyong the established limits of {llim:.2f} and {hlim:.2f} celsius degrees\n')
    elif value < llim:
        value = llim
        print(f'Temperature beyong the established limits of {llim:.2f} and {hlim:.2f} celsius degrees\n')    
    gs.SETPOINT_T = value 
def get_currentT():
    return gs.CURRENT_T 
def pid_init(temperature):
    pid_on()
    pid_stop()
    gs.SETPOINT_T = temperature
    thread = Thread(target = pid_controller, args=(gs.SETPOINT_T,gs.MODE_HEATING, gs.MAX_A,))
    thread.daemon = True
    thread.start()
    
if __name__ is '__main__':
    print('Functions for the pid loaded, please start it using pid_init()\n')