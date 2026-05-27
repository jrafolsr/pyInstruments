#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IVL snapshots with temperature swing between two setpoints.

Protocol per voltage in list_voltages:
    1. Drive V_bias at T1, logger running. Wait for steady-state rate
       condition on the LEC (same criterion as the original script).
    2. Ramp setpoint T1 -> T2. Logger keeps running, LEC stays biased,
       T(t) is captured in the logger file. Wait for thermal stabilization
       at T2 (|T - T2| < tol for hold_time seconds, with a hard timeout).
    3. Perform the I-V sweep at T2 (sweep_and_log -- this briefly stops the
       logger and restarts it after).
    4. Ramp back to T1. Wait for thermal stabilization at T1 before moving
       on to the next voltage.

The PID temperature controller runs in its own daemon thread for the
entire script; the script only writes to tc.setpoint and reads tc.current_T.
"""

from pyInstruments.ivl_snapshots import SweepMyLEC
from pyInstruments.pid import TemperatureControllerBipolar
from time import sleep, monotonic
from datetime import datetime
from pathlib import Path
from threading import Thread
import numpy as np
import shutil

#%%

# =============================================================================
# Experiment configuration
# =============================================================================

# --- Output folder / file id ------------------------------------------------
folder = Path(r'C:\Users\JOANRR\OneDrive - Umeå universitet\Documents\25_snaphsots\temperature')
file_id = 'Li_Thushar_01'

# --- LEC bias staircase -----------------------------------------------------
mode = 'CV'                              # 'CV' only, for now
list_voltages = [2.75, 3.00, 3.25]
N_staircase = 1
staircase_downscan = True
if staircase_downscan:
    list_voltages = list_voltages + list_voltages[-2::-1]

# --- Temperature swing ------------------------------------------------------
T1 = 30.0       # Holding / driving temperature in deg C
T2 = 5.0       # Snapshot temperature in deg C (where the sweep is taken)
T_park = 20.0   # Safe parking temperature at the very end of the script

# Thermal stabilization criterion: |T - setpoint| < T_tol for T_hold_time
# consecutive seconds. Hard timeout T_max_wait stops the wait either way.
T_tol = 0.3                 # deg C
T_hold_time = 30.0          # s of being within tol before we declare "stable"
T_max_wait = 10 * 60.0      # s, hard timeout per ramp
T_poll_dt = 0.5             # s, how often we poll current_T

# --- Rate condition at T1 (same idea as the original script) ----------------
rate_condition = 1e-5       # 1/s for CV mode (dj/dt / j)
min_time_per_voltage_step = 120.0    # s, min hold at V_bia /T1 before T2 ramp
max_time_per_voltage_step = 45*60   # s, hard cap on the wait at T1

# --- Optional pre-bias ------------------------------------------------------
run_prebias        = True
mode_prebias       = 'CC'
bias_prebias_input = 0.4              # mA if CC, V if CV
max_time_prebias   = 30*60
min_time_prebias   = 300
condition_prebias  = 1              # mV/min if CC, 1/s if CV

bias_prebias = bias_prebias_input if mode_prebias == 'CV' else bias_prebias_input / 1000.0

# --- After-sweep recovery time (LEC at V_bias, T back to T1) ----------------
time_after_sweep = 60.0    # s; on top of waiting for T to reach T1

# --- I-V sweep parameters ---------------------------------------------------
Vstart = 0.0
Vend = 5.0
step = 0.25
sweep_downscan = True
sweep_ranging = 'AUTO'
sweep_delay = 0.020
sweep_nplc = 1
sweep_pd_range = 'AUTO'
sweep_pd_nplc = sweep_nplc

if max(list_voltages) > Vend:
    print(f'The fast I-V sweep does not cover the max Vbias input '
          f'{Vend} V vs Vbias = {max(list_voltages)}')
    flag_continue = bool(input('\tAbort and fix it -> 0\n\tContinue -> 1\n'))
    if not flag_continue:
        raise ValueError('Stopping the script')

sweep_voltage = np.concatenate([
    np.arange(Vstart, 1.5, 0.3),
    np.arange(1.5, 2.50, 0.1),
    np.arange(2.50, Vend + 0.01, step),
])
if sweep_downscan:
    sweep_voltage = np.concatenate([sweep_voltage, sweep_voltage[-2::-1]])

# --- Instrument resources ---------------------------------------------------
resource_led = 'GPIB0::25::INSTR'
resource_pd  = 'GPIB0::26::INSTR'
resource_dmm = 'GPIB0::23::INSTR'    # Pt100 readout
resource_tec = 'GPIB0::5::INSTR'    # Keithley 24XX driving the Peltier

pd_bias = -5.0

# --- Temperature controller config -----------------------------------------
tc_kwargs = dict(
    setpoint=T1,
    max_poutput=2.00,
    current_compliance=1.2,
    multimeter_addr=resource_dmm,
    sourcemeter_addr=resource_tec,
    R0=100,
)
pid_loop_dt = 0.5    # s, sleeping_time in tc.run()


# =============================================================================
# Helpers
# =============================================================================

def wait_for_temperature(tc, target, tol=T_tol, hold_time=T_hold_time,
                         max_wait=T_max_wait, poll_dt=T_poll_dt, verbose=True):
    """Block until |tc.current_T - target| < tol for `hold_time` consecutive
    seconds, or until `max_wait` elapses.

    Returns
    -------
    reached : bool
        True if the stabilization criterion was met, False on timeout.
    """
    t0 = monotonic()
    in_band_since = None

    while (monotonic() - t0) < max_wait:
        T = tc.current_T
        within = (T is not None) and np.isfinite(T) and (abs(T - target) <= tol)

        if within:
            if in_band_since is None:
                in_band_since = monotonic()
            held = monotonic() - in_band_since
            if verbose:
                print(f'\rT-wait: target={target:6.2f} C  T={T:6.2f} C  '
                      f'in-band {held:5.1f}/{hold_time:.0f}s  '
                      f'elapsed {monotonic()-t0:6.1f}s', end='\r')
            if held >= hold_time:
                if verbose:
                    print()  # newline after the carriage-return spam
                return True
        else:
            in_band_since = None
            if verbose:
                print(f'\rT-wait: target={target:6.2f} C  T={T:6.2f} C  '
                      f'(out of band)              '
                      f'elapsed {monotonic()-t0:6.1f}s', end='\r')

        sleep(poll_dt)

    if verbose:
        print(f'\nWARNING: T-wait timeout after {max_wait:.0f} s, '
              f'T={tc.current_T:.2f} C, target={target:.2f} C')
    return False


# =============================================================================
# Folder / log setup
# =============================================================================

folder = folder / file_id
if not folder.exists():
    folder.mkdir(parents=True)

logfile = folder / (file_id + '_intervals.log')
with open(logfile, 'w') as f:
    f.write('Total_time[s]\tEllapsed_time[s]\tVoltage[V]\tCurrent[A]\t'
            'Photocurrent[A]\trate[1/s or mV/min]\tCondition_Status\t'
            'T_at_sweep[C]\tT_reached\tPhase\tRun#\n')


def log_interval(m, rate, condition_flag, T_at_sweep, T_reached, phase, run_idx):
    """Append a row to the intervals log."""
    with open(logfile, 'a') as f:
        f.write('{:.2f}\t{:.2f}\t{:.4f}\t{:10.6e}\t{:10.6e}\t{:8.4e}\t{}\t'
                '{:6.2f}\t{}\t{}\t{:02d}\n'.format(
                    m.main_timer.ellapsed_time(),
                    m.sub_timer.ellapsed_time(),
                    m.voltage_arr[-1],
                    m.current_arr[-1],
                    m.photocurrent_arr[-1],
                    rate,
                    condition_flag,
                    T_at_sweep,
                    T_reached,
                    phase,
                    run_idx))


# =============================================================================
# Bring up instruments
# =============================================================================

# LEC + photodiode SMUs
m = SweepMyLEC(resource_led, resource_pd, output_folder=folder)
kwargs_staircase = dict(reset=True, nplc=1, aver=False, Ncount=1, fw=False)
kwargs_pd = dict(kwargs_staircase)
kwargs_pd['cmpl'] = 100e-6
m.pd_config(pd_bias, **kwargs_pd)

# Temperature controller -- configure, then launch its run() in a daemon thread
tc = TemperatureControllerBipolar()
tc.configurate(**tc_kwargs)
tc.set_setpoint(T1)
tc.pid_on()

# CHANGED vs the original script: the PID controller has a blocking run()
# loop, so we hand it its own thread. tc.current_T gets updated in there.
pid_thread = Thread(target=tc.run, kwargs=dict(sleeping_time=pid_loop_dt),
                    daemon=True)
pid_thread.start()

# Give the PID a couple of cycles to populate current_T before we start
# checking it.
sleep(2.0)
print(f'PID thread alive: {pid_thread.is_alive()}, '
      f'current_T={tc.current_T:.2f} C, setpoint={tc.setpoint:.2f} C')

# Wait for the system to reach T1 before doing anything else.
print(f'\n--- Waiting for initial T1={T1:.2f} C ---')
wait_for_temperature(tc, T1)


# =============================================================================
# Main protocol
# =============================================================================

rate_condition_flag = False

try:
    # ---------- Pre-bias --------------------------------------------------
    if run_prebias:
        print(f'\n--- Running prebias protocol at {mode_prebias} ---')
        if mode_prebias == 'CC':
            m.configure_I(bias_prebias, **kwargs_staircase)
        elif mode_prebias == 'CV':
            m.configure_V(bias_prebias, **kwargs_staircase)
        else:
            raise ValueError(f'Mode "{mode_prebias}" not implemented '
                             f'(only "CV" or "CC")')

        timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss_")
        logger_filename = timestamp + file_id + f'_prebias{mode_prebias}.dat'
        m.run_logger_thread(logger_filename)

        rate_condition_flag = False
        while m.sub_timer.ellapsed_time() < max_time_prebias:
            condition, rate = m.check_rate_condition(condition_prebias)
            if condition and not rate_condition_flag:
                print(f'\nINFO: Prebias rate condition reached with '
                      f'{rate:.2e} at {m.sub_timer.ellapsed_time():.2f} s')
                rate_condition_flag = True
            if rate_condition_flag and m.sub_timer.ellapsed_time() >= min_time_prebias:
                print(f'\nINFO: Prebias rate + min_time condition reached '
                      f'with {rate:.2e} at '
                      f'{m.sub_timer.ellapsed_time():.2f} s')
                break

        m.stop_logger()
        m.thread.join()
        if not rate_condition_flag:
            print(f'\nINFO: Prebias finished by timeout {max_time_prebias:.0f} s, '
                  f'last rate {rate:.2e}')

    # ---------- Staircase + T-swing loop ----------------------------------
    print(f'\n--- Running staircase + T-swing protocol at {mode} ---')

    # Set the first bias, start the logger thread (this is the "permanent"
    # LEC logger -- it runs for the entire staircase, only sweep_and_log
    # stops it briefly).
    m.configure_V(list_voltages[0], **kwargs_staircase)

    timestamp = datetime.now().strftime("%Y-%m-%dT%Hh%Mm%Ss_")
    logger_filename = timestamp + file_id + '_staircase_run1.dat'
    m.run_logger_thread(logger_filename)

    for k in range(1, N_staircase + 1):
        logger_filename = timestamp + file_id + f'_staircase_run{k}.dat'

        for i, voltage in enumerate(list_voltages):
            print(f'\n=== Run #{k}, step {i+1}/{len(list_voltages)}: '
                  f'V_bias = {voltage:.2f} V ===')

            # --- 1. Drive at T1, wait for LEC steady state ----------------
            tc.set_setpoint(T1)            # make sure we are at T1
            m.request_bias_update(voltage)
            sleep(0.2)

            rate_condition_flag = False
            rate = np.nan
            print(f'Holding V_bias={voltage:.2f} V at T1={T1:.2f} °C, '
                  f'waiting for LEC steady state...')
            while m.sub_timer.ellapsed_time() < max_time_per_voltage_step:
                condition, rate = m.check_rate_condition(
                    rate_condition, check_last_n_seconds=30)
                if (condition and not rate_condition_flag
                        and m.sub_timer.ellapsed_time() >= 30):
                    print(f'\nINFO: LEC steady state at {rate:.2e} 1/s, '
                          f't={m.sub_timer.ellapsed_time():.2f} s')
                    rate_condition_flag = True
                if (rate_condition_flag and
                        m.sub_timer.ellapsed_time() >= min_time_per_voltage_step):
                    print(f'\nINFO: LEC steady state + min hold met at '
                          f't={m.sub_timer.ellapsed_time():.2f} s')
                    break

            if not rate_condition_flag:
                print(f'\nINFO: LEC hold ended by timeout '
                      f'{max_time_per_voltage_step:.0f} s, last rate {rate:.2e}')

            log_interval(m, rate, rate_condition_flag,
                         T_at_sweep=tc.current_T, T_reached=True,
                         phase='hold_T1', run_idx=k)

            # --- 2. Ramp T1 -> T2, logger keeps running -------------------
            print(f'\nRamping temperature: T1={T1:.2f} -> T2={T2:.2f} °C')
            tc.set_setpoint(T2)
            T2_reached = wait_for_temperature(tc, T2)
            T_at_sweep = tc.current_T

            log_interval(m, rate, rate_condition_flag,
                         T_at_sweep=T_at_sweep, T_reached=T2_reached,
                         phase='reached_T2', run_idx=k)

            # --- 3. I-V sweep at T2 ---------------------------------------
            print(f'\nPerforming sweep at T={T_at_sweep:.2f} C, '
                  f'V_bias={voltage:.2f} V')
            sweeper_filename = file_id + f'_run{k}_T2={T2:.1f}C'
            m.sweep_and_log(
                np.append(sweep_voltage, voltage),
                voltage,
                logger_filename,
                logger_aver=False, logger_Ncount=1, logger_nplc=1,
                sweep_fileid=sweeper_filename,
                sweep_ranging=sweep_ranging,
                sweep_reset=False,
                sweep_delay=sweep_delay,
                sweep_nplc=sweep_nplc,
                sweep_pd_range=sweep_pd_range,
                sweep_pd_nplc=sweep_pd_nplc,
            )

            # --- 4. Ramp back to T1 and let LEC recover -------------------
            print(f'\nRamping temperature back: T2={T2:.2f} -> T1={T1:.2f} C')
            tc.set_setpoint(T1)
            T1_reached = wait_for_temperature(tc, T1)

            log_interval(m, rate, rate_condition_flag,
                         T_at_sweep=tc.current_T, T_reached=T1_reached,
                         phase='back_to_T1', run_idx=k)

            print(f'\nPost-sweep recovery: holding at T1 for '
                  f'{time_after_sweep:.0f} s')
            t_recover = monotonic()
            while (monotonic() - t_recover) < time_after_sweep:
                sleep(0.1)

    print('\nCheckpoint 1: staircase loop complete')
    m.bias_setpoint = list_voltages[0]
    sleep(0.05)
    print('Checkpoint 2: stopping logger')
    m.stop_logger()

except KeyboardInterrupt:
    print('\nINFO: Terminating program (KeyboardInterrupt)')
except Exception as e:
    print(e)
    print('\nINFO: Terminating program (exception above)')

# =============================================================================
# Cleanup
# =============================================================================

sleep(0.05)
print('\nCheckpoint 3: parking instruments')

# Stop the LEC logger if it is still running
try:
    m.stop_logger()
except Exception as e:
    print(f'(non-fatal) m.stop_logger raised: {e}')

m.outpoff()
m.pd_outpoff()

# Ramp temperature back to a safe parking point before killing the PID.
# CHANGED: don't just pid_off() immediately -- that would cut the Peltier
# drive and let the stage drift uncontrolled. Ramp to T_park first.
# print(f'Ramping temperature to park point T_park={T_park:.2f} C before '
#       f'shutting down PID')
# tc.set_setpoint(T_park)
# wait_for_temperature(tc, T_park, max_wait=10 * 60.0)
tc.pid_off()
pid_thread.join(timeout=5.0)
if pid_thread.is_alive():
    print('WARNING: PID thread did not exit within 5 s of pid_off()')

# Copy this script to the data folder for traceability (same as original)
timestamp = datetime.now().strftime("%Y-%m-%d")
shutil.copy(__file__, folder / f'{timestamp}_measurement_script.py')

print('INFO: Program terminated.')
