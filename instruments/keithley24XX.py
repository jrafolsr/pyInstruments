# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 16:45:15 2019

@author: JOANRR
"""
from ..resources import sourcemeter
from numpy import array

class keithley24XX(sourcemeter):
    def __init__(self, resource, termination = '\r'):
        sourcemeter.__init__(self,resource, termination = termination)
        if (self.identify[0:34] == "KEITHLEY INSTRUMENTS INC.,MODEL 24"):
            print('You have connected succesfully with a %s' % self.identify[0:36])
        else:
            raise  Exception('Not able to connect with a 24XX family sourcemeter')
    def mode_pulse(self,curr_list,tpulse,term = 'FRONT'):
        """This method implements a pulse generated from the current list from the first argument
        with a time length of tpulse"""
        
        n_curr = len(curr_list)
        cmdcurr = ":SOUR:LIST:CURR " 
        for i, curr in enumerate(curr_list):
            if i < n_curr -1:
                cmdcurr = cmdcurr + "{:.6f},".format(curr)
            else:
                cmdcurr = cmdcurr + "{:.6f}".format(curr)
        self.inst.write("*RST")                  # Reset instrument to default parameters.
        self.inst.write(":ROUT:TERM %s" % term)     # Set the route to term front/rear
        self.inst.write(":SENS:FUNC:OFF:ALL")
        self.inst.write(":SOUR:FUNC:MODE CURR")       # Select current source function.
        self.inst.write(":SOUR:CURR:MODE LIST")  # Set mode list, an strategy to do a pulse
        self.inst.write(cmdcurr) # The command to input the list
        self.inst.write(":SOUR:DEL %.6e" % (tpulse))
        #inst.write(":SOUR:CURR 0.00")       # Set source to output 10mA.
        self.inst.write(":SOUR:CLE:AUTO ON")     # Enable source auto output-off.
        #inst.write(":SENS:VOLT:PROT 10")    # Set 10V compliance limit.
        self.inst.write(":TRIG:COUN {:d}".format(n_curr))         # Set to perform one measurement.
    def mode_ifix_configure(self,term = 'FRONT', fw = True, cmpl = 21.0, aver = True,\
                            Ncount = 10, beeper = True, nplc = 1, sens = True,\
                            curr_range = None):
        """Configures the 2400 to deliver a fix intensity and measure the voltage drop. 
        Optional arguments:
            - term = 'FRONT': The default terminal is FRONT. REAR can also be passed.
            - fw = True: 4-wire measurement or 2-wire
            - compl = 10: Set the compliance in volts, default is 10 V.
            - aver = True: Enables the average filter. Default is true.
            - Ncount = 10: Number of samples to average in case filter is enabled.
            - beeper = True: Enables or disables the beeper 
            - nplc = 1: Light cycles
            HAVE FUN! """
        self.inst.write("*RST")                  # Reset instrument to default parameters.
        self.inst.write(":SYSTem:TIME:RESet")   # Reset the time of the sourcemeter
        self.inst.write(":SYST:BEEP:STAT %i" % beeper) # Turn on/off the beeper
        self.inst.write(":ROUT:TERM %s" % term)     # Set the route to term front/rear
        self.inst.write(":SENS:RES:MODE MAN")    # Select manual ohms mode.
        self.inst.write(":SYST:RSEN %i" % fw)         # Select four wire measuremnt ohms mode.
        self.inst.write(":SOUR:FUNC CURR")       # Select current source function.
        self.inst.write(":SOUR:CURR 0.00")       # Set source to output 10mA.
        self.inst.write(":SOUR:CLE:AUTO OFF")     # Enable source auto output-off.
        if curr_range is not None:
            self.inst.write(":SOUR:CURR:RANG {:.6e}".format(curr_range))        
        self.inst.write(":SENS:VOLT:PROT %.2f" % cmpl)    # Set 10V compliance limit.
        self.inst.write(":TRIG:COUN 1")         # Set to perform one measurement.
        self.inst.write(":SENS:AVER:TCON REP")   # Set filter to repeating average
        self.inst.write(":SENS:AVER:COUNT %i" % Ncount)   # Set filter to repeating to 10 measurements
        self.inst.write(":SENS:AVER:STATE %i" % aver)  # Enable fiLter
        self.inst.write(':SENS:FUNC "VOLT"')     # Select ohms measurement function.
#        self.inst.write(':SENS:FUNC:ON "VOLT","CURR"')
        self.inst.write(":SENS:VOLT:NPLC %.3f" % nplc)      # Set measurement speed to 1 PLC.
        self.inst.write(":SENS:VOLT:RANG:AUTO ON")  # Auto range ON
        self.inst.write(":SYST:AZER:STAT ON")       # Auto-zero on
#        self.inst.write(":SYST:AZER:CACH:STAT ON")
        if not sens:
            print('All sens function have been turned off')
            self.inst.write("SENS:FUNC:OFF:ALL")
            
    def mode_ifix_setcurr(self,curr, curr_max = 0.05, curr_min = -0.05):
        """ Sends the order to the sourcemeter to inject the current 'curr' in A.
        Option arguments:
            - curr_max = 0.1: sets the maximum limit to be injected, to protect the
                                device.
            - curr_min = 0.00: sets the minimum injected current, to polarize a device.
        """

        # Set the current value in A
        if curr_min < curr < curr_max:
            self.inst.write(":SOUR:CURR %.6f" % curr)
        elif curr > curr_max:
            self.inst.write(":SOUR:CURR %.6f" % curr_max)
            print('WARNING: You have reached a software high current limit. Change it with curr_max argument')
        else:
            self.inst.write(":SOUR:CURR %.6f" % curr_min)
            print('WARNING: You have reached a software low current limit. Change it with curr_min argument')

    def mode_ifix_read(self):
        """Deprecated"""
        print('This method is deprecated, use de read() method instead. Does the same')
        return self.inst.query_ascii_values('READ?', container=array)
    def read(self):
        """ Sends the query read, and returns an array, depending on the type of measurement implemented"""
        return self.inst.query_ascii_values('READ?', container=array)
    def init(self):
   #inst.write(":TRIG:DEL %.6f" % (trigger_del/1000.0))
        self.inst.write("INIT")
    def mode_vfix_configure(self,term = 'FRONT', fw = False, cmpl = 0.050, beeper = True, aver = True,\
                            Ncount = 10, nplc = 1, sens = True,\
                            volt_range = None):
        """Configures the 2400 to deliver a fix voltage and that's it for the moment" 
        Optional arguments:
            - term = 'FRONT': The default terminal is FRONT. REAR can also be passed.
            - compl = 10: Set the compliance in volts, default is 10 V.
            - beeper = True: Enables or disables the beeper 
            HAVE FUN! """
        print('HAHAHAHAHA')
        self.inst.write("*RST")                  # Reset instrument to default parameters.
        self.inst.write(":SYSTem:TIME:RESet")   # Reset the time of the sourcemeter
        self.inst.write(":SYST:BEEP:STAT %i" % beeper) # Turn on/off the beeper
        self.inst.write(":ROUT:TERM %s" % term)     # Set the route to term front/rear
        self.inst.write(":SYST:RSEN %i" % fw)         # Select four wire measuremnt ohms mode.       
        self.inst.write(":SOUR:FUNC VOLT")       # Select current source function.
        self.inst.write(":SOUR:VOLT 0.00")       # Set source to output 0.0V.
        self.inst.write(":SOUR:CLE:AUTO OFF")     # Enable source auto output-off.
        if volt_range is not None:
            self.inst.write(":SOUR:VOLT:RANG {:.6e}".format(volt_range))
            
        self.inst.write(":TRIG:COUN 1")         # Set to perform one measurement.
        self.inst.write(":SENS:AVER:TCON REP")   # Set filter to repeating average
        self.inst.write(":SENS:AVER:COUNT %i" % Ncount)   # Set filter to repeating to 10 measurements
        self.inst.write(":SENS:AVER:STATE %i" % aver)  # Enable fiLter
        self.inst.write(":SENS:VOLT:NPLC %.3f" % nplc)      # Set measurement speed to 1 PLC.
        self.inst.write(":SENS:VOLT:RANG:AUTO ON")  # Auto range ON
        self.inst.write(":SENS:CURR:PROT:LEV %.3g" % cmpl)    # Set the compliance limit.
        
        if not sens:
            print('All sens function have been turned off')
            self.inst.write(":SENS:FUNC:OFF:ALL")
        
    def mode_vfix_setvolt(self,volt):
        """ Sends the order to the sourcemeter to set the voltage 'volt' in V."""
        self.inst.write(":SOUR:VOLT %.6f" % volt)
    def outpoff(self):
        self.inst.write(":OUTP OFF")
    def outpon(self):
        self.inst.write(":OUTP ON")
    def outpstate(self):
        """Checks the output state"""
        return bool(self.inst.query_ascii_values(":OUTPut?")[0])
    def close(self):
        self.inst.close()
    def check_volt_compliance(self):
        return bool(self.inst.query_ascii_values(':VOLTage:PROTection:TRIPped?')[0])
    def check_curr_compliance(self):
        return bool(self.inst.query_ascii_values(':CURRent:PROTection:TRIPped?')[0])