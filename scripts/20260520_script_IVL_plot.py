#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 13:16:26 2026

@author: pi
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import seaborn as sns


folder = Path('/home/pi/Documents/data/Sri/22-SP02-04b')
output_folder = folder.parent
run = 1

file_prebias = list(folder.glob('*prebias*.dat'))[0]
file_staircase = list(folder.glob(f'*staircase*run{run:d}.dat'))[0]
files_IVL = list(folder.glob(f'*sweep*run{run:d}.dat'))
files_IVL.sort()


# Prebias

fig, ax = plt.subplots()

time, voltage, current,_, photocurrent, _ = np.loadtxt(file_prebias, unpack=True)

line1, = ax.plot(time, voltage, 'C0', label = 'voltage')

ax2 = ax.twinx()

line2, = ax2.plot(time, -photocurrent, 'C1', label = 'photocurrent')

ax.set_xlabel('Time (s)')
ax.set_ylabel('Voltage (V)')
ax2.set_ylabel('Photocurrent (a.u.)')

median_current = np.median(current*1000)
ax.set_title(f'Prebias - CC at {median_current:.2f} mA')
lines = [line1, line2]


ax.legend(lines, [l.get_label() for l in lines])

ax.set_title(folder.stem)
fig.savefig(output_folder / f'{folder.stem}_prebias.png', bbox_inches='tight', dpi=300)

# Staircase
fig,  axes = plt.subplots(nrows=3, sharex=True, figsize=(6,8))
ax, ax2, ax3 = axes
[a.grid(True) for a in axes]
time, voltage, current,_, photocurrent, _ = np.loadtxt(file_staircase, unpack=True)

line1, = ax.plot(time, voltage, 'C3', label = 'voltage')


line2, = ax2.plot(time, current*1000, 'C0', label = 'current')


line3, = ax3.plot(time, -photocurrent, 'C1', label = 'photocurrent')

ax3.set_xlabel('Time (s)')
ax.set_ylabel('Voltage (V)')
ax2.set_ylabel('Current (mA)')
ax3.set_ylabel('Photocurrent (a.u.)')

median_current = np.median(current*1000)
ax.set_title(f'Staircase - CV from {voltage.min():.2f} -  {voltage.max():.2f} V')

ax.set_title(folder.stem)
fig.savefig(output_folder / f'{folder.stem}_staircase.png', bbox_inches='tight', dpi=300)


#lines = [line1, line2]

#ax.set_yscale('log')
#ax2.set_yscale('log')
#ax.legend(lines, [l.get_label() for l in lines])


N = len(files_IVL) //2 +1
colors = sns.color_palette('rocket', n_colors=N)
mfc = [None]*N
colors = colors + colors[::-1][1:]
mfc = mfc + ['white']*(N-1)

fig, [ax, ax2] = plt.subplots(ncols = 2, figsize = (8,4), gridspec_kw=dict(wspace  = 0.4))
ax.set_xlabel('Voltage (V)')
ax2.set_xlabel('Voltage (V)')
ax.set_ylabel('Current (mA)')
ax2.set_ylabel('Photocurrent (a.u.)')
ax.set_yscale('log')
ax2.set_yscale('log')

for i, file in enumerate(files_IVL):
    voltage, current, photocurrent, _ = np.loadtxt(file, unpack=True)
    bias = float(file.stem.split('Vsp=')[1][:4])
    y = np.abs(current*1000)
    ax.plot(voltage, y, '.-', c=colors[i], label = f'{bias:.2f} V', mfc=mfc[i])
    y2 = np.abs(photocurrent)
    ax2.plot(voltage, y2, '*-', c=colors[i], label = f'{bias:.2f} V', mfc=mfc[i])

ax.legend()

ax.set_title(folder.stem)
fig.savefig(output_folder / f'{folder.stem}_snapshots.png', bbox_inches='tight', dpi=300)


