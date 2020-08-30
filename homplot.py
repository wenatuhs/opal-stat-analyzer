#!/opt/python/python-2.7.3/bin/python
# -*- coding: utf-8 -*-
# Adapated by Zhang Zhe

import os
import json

import numpy as np
import matplotlib.pyplot as plt

from homdict import *

spParams = {
    'home': './',
}

def plotHBUNCH():
    options = ['enx', 'sigma_x', 'Bz']
    # read setting file
    try:
        fset = file('hsettings.json')
        settings = json.load(fset)
        fset.close()
        try:
            options = settings['HBUNCH']
        except KeyError:
            print "No settings for HBUNCH in setting file, using\
                   default settings!"
    except IOError:
        print "No setting file found, using default settings!"
    try:
        lo = [homdict[options[0]], homdict[options[1]], homdict[options[2]]]
    except IndexError:
        print "Setting file format error, using default settings!"
        options = ['enx', 'sigma_x', 'Bz']
        lo = [homdict[options[0]], homdict[options[1]], homdict[options[2]]]
    except KeyError:
        print "Some parameters in setting file don't exist in\
               'HBUNCH.OUT', using default settings!"
        options = ['enx', 'sigma_x', 'Bz']
        lo = [homdict[options[0]], homdict[options[1]], homdict[options[2]]]
    # set up figure properties
    fig = plt.figure(figsize=(10, 18))
    fig.suptitle('%s, %s & %s' % tuple(options), fontsize=14, 
                 fontweight='bold')
    ax1 = fig.add_axes([0.09, 0.69, 0.65, 0.27])
    ax2 = fig.add_axes([0.09, 0.37, 0.65, 0.27])
    ax3 = fig.add_axes([0.09, 0.05, 0.65, 0.27])

    ax1.set_yscale('log')
    ax2.set_yscale('log')
    #ax3.set_yscale('log')

    ax1.set(xlabel='z (m)', ylabel='%s (%s)' % \
            (options[0], lo[0][2]), xlim=(-0.02, 3))
    ax2.set(xlabel='z (m)', ylabel='%s (%s)' % \
            (options[1], lo[1][2]), xlim=(-0.02, 3))
    ax3.set(xlabel='z (m)', ylabel='%s (%s)' % \
            (options[2], lo[2][2]), xlim=(-0.02, 0.3))

    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)

    try:
        f = file(os.path.join(spParams['home'], 'HBUNCH.OUT'))
        data = f.readlines()[1:]
        X = [float(l.split()[0]) for l in data]
        try:
            Y1 = [float(l.split()[lo[0][0]]) for l in data]
            Y2 = [float(l.split()[lo[1][0]]) for l in data]
            Y3 = [float(l.split()[lo[2][0]]) for l in data]
        except IndexError:
            index = 0
            if lo[0][0] == 25:
                Y1 = [float(l.split()[8]) * float(l.split()[9]) / 100.0 for l in data]
                Y2 = [float(l.split()[lo[1][0]]) for l in data]
                Y3 = [float(l.split()[lo[2][0]]) for l in data]
            elif lo[1][0] == 25:
                Y2 = [float(l.split()[8]) * float(l.split()[9]) / 100.0 for l in data]
                Y3 = [float(l.split()[lo[2][0]]) for l in data]
            else:
                Y3 = [float(l.split()[8]) * float(l.split()[9]) / 100.0 for l in data]

        ax1.plot(X, Y1, label='HOMDYN')
        ax2.plot(X, Y2, label='HOMDYN')
        ax3.plot(X, Y3, label='HOMDYN')

        ax1.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fancybox=True,
                   prop={'size': 8}, shadow=True)

        plt.show()
    except IOError:
        print "No 'HBUNCH.OUT' file under home directory!"


if __name__ == '__main__':
    plotHBUNCH()


