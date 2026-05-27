# -*- coding: utf-8 -*-
"""
Temperature controller using a Keithley 24XX SMU (4-quadrant) for the Peltier.

Hardware setup notes
--------------------
The Keithley 2425 is a true 4-quadrant source: it sources/sinks both
positive and negative voltage natively. The PID drives the Peltier with
a signed voltage; positive heats, negative cools (or vice versa,
depending on which side of the Peltier the sample sits on).

No bridge wiring, no relay, no polarity-flip logic. The PID's signed
action goes straight to mode_vfix_setvolt.
"""

from time import sleep, monotonic
from pyInstruments.instruments import keysight34461A, keithley24XX   # CHANGED
from pyInstruments.pid import Pid
import datetime
from numpy import sqrt, isclose, nan
from threading import Lock
today = datetime.date.today().strftime("%d%m%Y")
from pathlib import Path
from pyInstruments import __file__ as module_folder
tempfile = Path(module_folder).parent / Path('temp/temp.dat')


def calc_temperature(R, R0=100.0, alpha=3.9083e-3, beta=-5.7750e-7):
    """Returns the temperature in °C according to the Standard Class B Pt100/1000."""
    return (-alpha + sqrt(alpha**2 - 4 * beta * (1 - R / R0))) / 2 / beta


class TemperatureControllerBipolar(object):
    def __init__(self):
        self.setpoint = nan
        self.current_T = nan
        self.lock = Lock()
        self.log_file = tempfile
        self.heating_ramp = 20    # K/min, used when current_T < setpoint
        self.cooling_ramp = 60    # K/min, used when current_T > setpoint

    # CHANGED: removed `heating` argument; added current_compliance.
    def configurate(self, setpoint=20.0, max_poutput=4.00,
                    current_compliance=1.2,
                    multimeter_addr='GPIB0::23::INSTR',
                    sourcemeter_addr='GPIB0::24::INSTR',
                    R0=100):
        """
        Parameters
        ----------
        setpoint : float
            Target temperature in °C.
        max_poutput : float
            Maximum |voltage| applied to the Peltier, in volts. Symmetric.
        current_compliance : float
            Current compliance (A). The Keithley clamps current at this value
            to protect the Peltier. 1.2 A is a safe limit for a 1 A Peltier.
        """
        self.setpoint = setpoint
        self.pid_running = False
        self.max_poutput = max_poutput
        self.R0 = R0

        self.mult = keysight34461A(multimeter_addr)
        # CHANGED: instantiate Keithley instead of agilent supply
        self.supply = keithley24XX(sourcemeter_addr)

        if R0 == 100:
            self.mult.config_ohms(rang=1000, nplc=1, count=5)
        else:
            self.mult.config_ohms(rang=10000, nplc=1, count=5)

        # CHANGED: symmetric limits for bipolar drive
        self.pmin = -1.0 * self.max_poutput
        self.pmax = +1.0 * self.max_poutput

        # CHANGED: configure Keithley as a fixed-voltage source with a
        # current compliance. Pick the 10 V voltage range -- gives us the
        # 3 A current capability, plenty of headroom for a 1 A Peltier.
        self.supply.mode_vfix_configure(
            term='FRONT',
            fw=False,                  # 2-wire is fine for driving a Peltier
            cmpl=current_compliance,   # current compliance
            beeper=False,              # quieter during long PID runs
            aver=False,                # we want the live reading, not averaged
            nplc=0.1,                  # fast readback for the PID loop
            sens=True,                 # we want to read back voltage AND current
            volt_range=2.1,             # 10 V range gives 3 A capability
            reset=True
        )
        # Park at 0 V before we enable the output
        self.supply.mode_vfix_setvolt(0.0)


    def set_current_limit(self, value):
        self.supply.set_current_compliance(value)
        print(f'INFO: Chaning the current compliance to {value:.4f}A')

    def run(self, sleeping_time=0.5):
        Kp = 1.0
        Ki = 0.05
        Kd = 0.0
        pid = Pid(Kp, Ki, Kd, ulimit=self.pmax, llimit=self.pmin)
        pid.clear()

        self.current_T = calc_temperature(self.mult.read(), self.R0).mean(axis=0)
        pid.set_setpoint(self.current_T)

        while self.pid_running:
            try:
                time1 = monotonic()

                # CHANGED: outpstate / outpon are the Keithley's methods
                if not self.supply.outpstate():
                    print('INFO: Turning on the Keithley output')
                    self.supply.outpon()

                # Keep the PID limits in sync with the user-visible max_poutput
                pid.ulimit = +1.0 * self.max_poutput
                pid.llimit = -1.0 * self.max_poutput

                T = calc_temperature(self.mult.read(), self.R0).mean(axis=0)

                # CHANGED: ramp dispatched on sign of (setpoint - T)
                error = self.setpoint - T
                if isclose(T, self.setpoint, 0, 0.5):
                    action = pid.update(T, self.setpoint)
                elif error > 0:
                    action = pid.update(
                        T, pid.setpoint + self.heating_ramp / 60.0 * pid.dt
                    )
                else:
                    action = pid.update(
                        T, pid.setpoint - self.cooling_ramp / 60.0 * pid.dt
                    )

                # CHANGED: signed action goes straight in. No abs(), no
                # polarity flag. The Keithley sources both polarities.
                self.supply.mode_vfix_setvolt(action)

                self.current_T = T
                self.current_action = action
                self.current_voltage = action

                # CHANGED: read back actual current from the Keithley.
                # READ? on a 24XX returns [V, I, R, t, status]; we want I.
                try:
                    measurement = self.supply.read()
                    self.current_intensity = float(measurement[1])
                except Exception:
                    # If a read fails mid-loop, don't crash the PID --
                    # just skip the readback for this iteration.
                    self.current_intensity = nan

                with self.lock:
                    with open(self.log_file, 'w') as f:
                        f.write(f'{T:5.2f}')

                while (monotonic() - time1) < sleeping_time:
                    sleep(0.01)

            except KeyboardInterrupt:
                print('INFO: Pid program interrupted in a safe way\n')
                break
            except Exception as e:
                print(e)
                break

        pid.clear()
        # CHANGED: park at 0 V and turn off
        self.supply.mode_vfix_setvolt(0.0)
        self.supply.outpoff()
        return None

    def pid_on(self):
        self.pid_running = True

    def pid_off(self):
        self.pid_running = False
        with self.lock:
            with open(self.log_file, 'w') as f:
                f.write('nan')

    def set_setpoint(self, value, min_value=-20, max_value=100):
        if value > max_value:
            value = max_value
            print(f'INFO: Temperature beyond the established limits of '
                  f'{min_value:.2f} and {max_value:.2f} °C\n')
        elif value < min_value:
            value = min_value
            print(f'INFO: Temperature beyond the established limits of '
                  f'{min_value:.2f} and {max_value:.2f} °C\n')
        self.setpoint = value


if __name__ == '__main__':
    print('Functions for the pid loaded (Keithley 24XX backend)\n')