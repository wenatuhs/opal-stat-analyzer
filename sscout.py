#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Adapated by Zhang Zhe

import os
import sys
import json
import argparse
from collections import OrderedDict

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

import peakfinder as pf
from progressbar import ProgressBar
from terminal import render 

from statdict import *


spParams = {
    # home directory
    'home': './', 
    # project name
    'name': 'cBandGun' 
}


class getslice:
    def __getitem__(self, idx): return idx[0]


def getSlice(s):
    return eval("getslice()[%s,]" % s)


def runCounter(start, end, step):
    start = float(start)
    end = float(end)
    step = float(step)
    num = 0
    sum = start
    while sum <= end:
        sum += step
        num += 1
    return num


def autoDetectProj():
    if os.path.exists(spParams['home']):
        folderlist = [f for f in os.listdir(spParams['home']) if
                      os.path.isdir(os.path.join(spParams['home'], f))]
        option = []
        projname = ""
        for folder in folderlist:
            fname = folder.split('_')[0]
            if fname in option:
                projname = fname
                break
            elif len(folder.split('_')) > 1:
                option.append(fname)
        if not projname:
            if len(option) == 1:
                projname = option[0]
            else:
                projname = spParams['name']

        spParams['name'] = projname


def showSimParas():
    try:
        filename = os.path.join(spParams['home'], spParams['name']+'.data')
        f = file(filename)
        dic = OrderedDict()
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            elif not line.startswith('#'):
                s = line.split()
                try:
                    dic[s[0]] = s[1]
                except IndexError:
                    pass
        f.close()
        print render('%(BLUE)s' + json.dumps(dic, sort_keys=False, indent=4, 
                                             separators=(',', ': ')) + '%(NORMAL)s')
    except IOError:
        print ".data file doesn't exist!"


def getSimFolders():
    """
    Get the list of simulation folders in home directory.

    keyword arguments:

    return -- A list giving all the simulation folders in home directory.

    """
    if os.path.exists(spParams['home']):
        folderlist = [f for f in os.listdir(spParams['home']) if
                   os.path.isdir(os.path.join(spParams['home'], f))]
        simfolders = [d for d in folderlist if d.startswith(spParams['name'])]
    else:
        simfolders = []

    return simfolders


def easyBackup(id, pb=None):
    pre = 'backup'
    simfolders = getSimFolders()
    if not pb:
        pb = ProgressBar(color='blue')
    # backup single folder with a specified id=i.
    def singleBackup(i, pb):
        # set progress bar
        suf = '\nbackup processing...'
        pb.render(0, 'preparing backup folders...'+suf)
        # prepare backup folders
        simfolder = simfolders[i]
        simdir = os.path.join(spParams['home'], simfolder)
        budir = os.path.join(pre, simfolder)
        os.makedirs(budir)
        namelist = [d for d in os.listdir(simdir) if 
                    os.path.isdir(os.path.join(simdir, d))
                    and d.startswith(spParams['name'])]
        size = len(namelist)
        if size:
            fail = 0
            for name in namelist:
                idx = namelist.index(name)
                pb.render(int(np.floor(float(idx - fail) / size * 100)), 
                          'backing up... %s/%s' % (idx + 1, size) + suf)
                _simdir = os.path.join(simdir, name)
                _budir = os.path.join(budir, name) 
                bufile = [f for f in os.listdir(_simdir) if f[-4:] == 'stat']
                if bufile:
                    os.makedirs(_budir) 
                    os.system('cp ' + os.path.join(_simdir, '*.stat ') + _budir)
                else:
                    pb.render(int(np.floor(float(idx) / size * 100)), 
                              'can\'t find stat files! %s/%s' % (idx + 1, size)
                              + suf)
                    fail += 1
            if not fail:
                pb.render(100, 'id=%s done!' % i)
            else:
                pb.render(int(np.floor(float(size - fail) / size * 100)),
                          'id=%s failed...' % i)
        else:
            bufile = [f for f in os.listdir(simdir) if f[-4:] == 'stat']
            busize = len(bufile)
            if busize:
                for buf in bufile:
                    buidx = bufile.index(buf)
                    pb.render(int(np.floor(float(buidx) / busize * 100)), 
                              'backing up... %s/%s' % (buidx + 1, busize) + suf)
                    os.system('cp ' + os.path.join(simdir, buf) + ' ' + budir)  
                pb.render(100, 'id=%s done!' % i)
            else:
                pb.render(0, 'id=%s failed... can\'t locate .stat files.' % i +
                          suf)
    # backup chosen folders    
    for i in id:
        singleBackup(i, pb)


def check(id, details=False):
    logs = []
    logpasses = []
    summaries = []
    simfolders = getSimFolders()
    # backup single folder with a specified id=i.
    def singleCheck(i):
        ifpass = True
        log = []
        logpass = []
        summary = ""
        numfail = 0
        numtotal = 0
        simfolder = simfolders[i]
        simdir = os.path.join(spParams['home'], simfolder)
        namelist = [d for d in os.listdir(simdir) if 
                    os.path.isdir(os.path.join(simdir, d))
                    and d.startswith(spParams['name'])]
        size = len(namelist)
        # consider the simulation folder is a single or a scan
        if size:
            numtotal = size
            for name in namelist:
                _simdir = os.path.join(simdir, name)
                statfile = [f for f in os.listdir(_simdir) if f[-4:] == 'stat']
                if not statfile:
                    numfail += 1
                    log.append(_simdir)
                else:
                    logpass.append(_simdir)
            summary = "id=%s, pass/total: %i/%i" % (i, numtotal - numfail, numtotal) 
            if numfail:
                ifpass = False
        else:
            statfile = [f for f in os.listdir(simdir) if f[-4:] == 'stat']
            statsize = len(statfile)
            numtotal = statsize
            if statsize:
                logpass.append(simdir)
                summary = "id=%s, pass/total: %i/%i" % (i, 1, numtotal) 
            else:
                log.append(simdir)
                summary = "id=%s, pass/total: %i/%i" % (i, 0, numtotal) 
                ifpass = False
        return log, logpass, summary, ifpass
    # check chosen folders    
    for i in id:
        log, logpass, summary, ifpass = singleCheck(i)

        if log:
            log = "id=%s, fail:" % i + '\n\t' + '\n\t'.join(log)
            log = render('%(RED)s' + log + '%(NORMAL)s')
            logs.append(log)
        else:
            logs.append(None)

        if logpass:
            logpass = "id=%s, pass:" % i + '\n\t' + '\n\t'.join(logpass)
            logpass = render('%(GREEN)s' + logpass + '%(NORMAL)s')
            logpasses.append(logpass)
        else:
            logs.append(None)

        if ifpass or details:
            summary = render('%(BLUE)s' + summary + '%(NORMAL)s')
        else:
            summary = render('%(RED)s' + summary + '%(NORMAL)s')
        summaries.append(summary)
    for i in range(len(summaries)):
        print summaries[i]
        if details:
            if logs[i]:
                print logs[i]
            if logpass[i]:
                print logpasses[i]


def mergeIDs(id):
    idlist = range(len(getSimFolders()))
    if not id:
        return idlist 
    else:
        idset = []
        for s in id:
            try:
                part = idlist[getSlice(s)]
            except IndexError: 
                print render('%(RED)s' + "id=%s doesn't exist!" % s + '%(NORMAL)s')
                continue
            if isinstance(part, int):
                idset.append(part)
            else:
                idset += part
        idset = sorted(set(idset))
    return idset


def parseSimName(name):
    """
    Parse a single simualtion folder's name to get the parameter's infomations.

    keyword arguments:
    name -- the name string of the simulation's name

    return -- Two lists, one contains all the scan parameter names, the other
        contains the values correlating to the names.

    """
    # remove the prefix (the project name) of the simfolder
    simname = ''.join(c for c in spParams['name'] if c != '_')
    tmp = name[len(simname):].split('=')
    var = []
    value = []
    for token in tmp:
        for i, c in enumerate(token):
            if c.isalpha():
                if i == 0:
                    var.append(token)
                    break
                elif c == 'e' or c =='E':
                    c_ = token[i + 1]
                    if c_.isalpha():
                        value.append(float(token[:i]))
                        var.append(token[i:])
                        break
                else:
                    value.append(float(token[:i]))
                    var.append(token[i:])
                    break
            elif i == len(token) - 1:
                value.append(float(token))

    return var, value


def parseScanName(name):
    """
    Parse a scan folder's name to get the parameter's infomations.

    keyword arguments:
    name -- the name string of the simulation's name

    return -- Two lists, one contains all the scan parameter names, the other
        contains the values correlating to the names.

    """
    # remove the prefix (the project name) of the simfolder
    tmp = name[len(spParams['name']):].split('=')
    var = []
    scan = []
    for token in tmp:
        idx = token.find('_')
        if idx == -1:
            scan.append(token)
        elif idx == 0:
            var.append(token[1:])
        else:
            scan.append(token[:idx])
            var.append(token[idx + 1:])

    return var, scan


def genSimLabel(folder, name):
    # the reason not parse simfolder for var but parse scanfolder for
    # var is the var name in simfolder name may not be the real name. say:
    # "FINSB01_RACC_pos" will become "SB01RACCpos" when runOPAL create the
    # simfolder
    if name:
        var = parseScanName(folder)[0]
        value = parseSimName(name)[1]
    else:
        var, value = parseSimName(folder)
    if var:
        label = var[0] + '=' +  str(value[0])
        for i in range(1, len(var)):
            if i % 2 == 1:
                label += ', ' + var[i] + '=' + str(value[i])
            else:
                label += '  \n' + var[i] + '=' + str(value[i])
    # for the single simulation without any specified parameters
    else:
        label = 'Specified by\n' + os.path.join(spParams['home'],
                                                spParams['name']+'.data') 

    return label


def genCompLabel(folder, name, spec):
    var = parseScanName(folder)[0]
    value = parseSimName(name)[1]
    var.pop(spec)
    value.pop(spec)
    if var:
        label = var[0] + '=' +  str(value[0])
        for i in range(1, len(var)):
            if i % 2 == 1:
                label += ', ' + var[i] + '=' + str(value[i])
            else:
                label += '  \n' + var[i] + '=' + str(value[i])
    else:
        label = 'Specified by\n' + os.path.join(spParams['home'],
                                                spParams['name']+'.data') 

    return label


def getPeaks(x, y, look=15):
    return pf.peakdetect(y, x, lookahead=look)


def genScanMap(id):
    try:
        simfolder = getSimFolders()[id]
    except IndexError:
        return None, [], [], {} 
    var = parseScanName(simfolder)[0]
    scanrange = []
    scandict = {}
    simname = ''.join(c for c in spParams['name'] if c != '_')
    if var:
        for v in var:
            scanrange.append([])
        for name in os.listdir(os.path.join(spParams['home'], simfolder)):
            if name.startswith(simname):
                value = parseSimName(name)[1]
                for i in range(len(var)):
                    scanrange[i].append(value[i])
                scandict[tuple(value)] = name
        for i in range(len(var)):
            scanrange[i] = sorted(list(set(scanrange[i])))
        scanshape = tuple([len(r) for r in scanrange])
        # generate the map
        scanmap = np.empty(scanshape, dtype='S64')
        for key in scandict.keys():
            idx = tuple([scanrange[i].index(key[i]) for i in range(len(var))])
            scanmap[idx] = scandict[key]
    else:
        scanmap = np.empty(1, dtype='S64')
        scanmap[0] = ''

    return simfolder, var, scanrange, scanmap


def showSimInfo(id):
    info = OrderedDict()
    info['project name'] = spParams['name']
    info['project path'] = spParams['home']
    scaninfo = []
    simfolders = getSimFolders()
    for i in range(0, len(simfolders)):
        if spParams['name'] != 'Gene':
            var, scan = parseScanName(simfolders[i])
            dic = OrderedDict()
            dic['id'] = i
            dic['project name'] = spParams['name']
            dic['project path'] = spParams['home']
            dic['simfolder path'] = os.path.join(spParams['home'], simfolders[i])
            # if no scan, show 'No Scan'
            if var:
                vardic = OrderedDict()
                for j in range(0, len(var)):
                    try:
                        float(scan[j])
                        vardic[var[j]] = scan[j] + ", num=1"
                    except ValueError:
                        start, end, step = tuple(scan[j].split(':'))
                        num = runCounter(start, end, step)
                        vardic[var[j]] = scan[j] + ", num=%i" % num
                dic['scaned variables'] = vardic
            else:
                dic['scaned variables'] = 'No Scan'
            scaninfo.append(dic)
        else:
            dic = OrderedDict()
            dic['id'] = i
            dic['project name'] = spParams['name']
            dic['project path'] = spParams['home']
            dic['simfolder path'] = os.path.join(spParams['home'], simfolders[i])
            scaninfo.append(dic)
    info['simulation folders'] = scaninfo 
    # print chosen sim's info
    for i in id:
        dic = info['simulation folders'][i]
        print render('%(BLUE)s' + json.dumps(dic, sort_keys=False, indent=4, 
                                             separators=(',', ': ')) + '%(NORMAL)s')


def listSimFolders(id):
    simfolders = getSimFolders()
    for i in id:
        simfolder = simfolders[i]
        print render('%(BLUE)s' + simfolder + ':%(NORMAL)s')
        print render('%(BLUE)s' + '\t' + 
                     '\n\t'.join([name for name in 
                                os.listdir(os.path.join(spParams['home'], simfolder)) 
                                if name.startswith(spParams['name'])]) + '%(NORMAL)s')


def plotGene2D(args, id, save, pb=None):
    options = ['rms_x', 'rms_y', 'rms_s']
    # set progress bar
    suf = '\ngene 2d plotting...'
    if not pb:
        pb = ProgressBar(color='blue')
    # read the settings file
    pb.render(0, 'reading plot settings...' + suf)
    try:
        fset = file('ssettings.json')
        settings = json.load(fset)
        fset.close()
        try:
            options = settings['geneplot']
        except KeyError:
            pb.render(0, "no settings for geneplot in settings file, using\
                      default settings..." + suf)
    except IOError:
        pb.render(0, 'no settings file, using default settings...' + suf)
    # set figure properties
    figname = 'GENE_id' + str(id) + '=[' +  ','.join(args) + ']'
    fig = plt.figure(num=figname, figsize=(10,18))
    ax1 = fig.add_axes([0.09, 0.69, 0.65, 0.27])
    ax2 = fig.add_axes([0.09, 0.37, 0.65, 0.27])
    ax3 = fig.add_axes([0.09, 0.05, 0.65, 0.27])
    ax1.set_yscale('log')
    ax2.set_yscale('log')
    #ax3.set_yscale('log')
    try:
        lo = [statdict[options[0]], statdict[options[1]], statdict[options[2]]]
    except IndexError:
        pb.render(0, 'settings file format error, using default settings...' + suf)
        options = ['rms_x', 'rms_y', 'rms_s']
        lo = [statdict[options[0]], statdict[options[1]], statdict[options[2]]]
    except KeyError:
        pb.render(0, "some parameters in settings file don't exist in\
                  statdict, using default settings..." + suf)
        options = ['rms_x', 'rms_y', 'rms_s']
        lo = [statdict[options[0]], statdict[options[1]], statdict[options[2]]]
    fig.suptitle('%s, %s & %s' % tuple(options), fontsize=14,
                 fontweight='bold')
    ax1.set(xlabel='z (m)', ylabel='%s (%s)' % (options[0], lo[0][2]))
    ax2.set(xlabel='z (m)', ylabel='%s (%s)' % (options[1], lo[1][2]))
    ax3.set(xlabel='z (m)', ylabel='%s (%s)' % (options[2], lo[2][2]))
    #ax3.set(xlabel='z (m)', ylabel='dE_x (MeV)')
    ax1.grid(True)
    ax2.grid(True)
    ax3.grid(True)
    # grab simulation file list from the sim-root directory
    simfolder = getSimFolders()[id]
    # travel all the chosen ids
    choosize = len(args)
    for n in args:
        realdir = os.path.join(spParams['home'], simfolder, 'id='+n)
        realfolder = [f for f in os.listdir(realdir) if
                      os.path.isdir(os.path.join(realdir, f))][0]
        realname = [na for na in os.listdir(os.path.join(realdir, realfolder)) if
                    os.path.splitext(na)[1] == '.stat'][0]
        filename = os.path.join(realdir, realfolder, realname)
        simlabel = 'id=' + n 
        # grab data from simulation files
        try:
            f = file(filename)
        except IOError:
            continue
        flag = 0
        X= []
        Y1 = []
        Y2 = []
        Y3 = []
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            s = line.split()
            if flag:
                X.append(float(s[1]))
                Y1.append(float(s[lo[0][0]])*float(lo[0][1]))
                Y2.append(float(s[lo[1][0]])*float(lo[1][1]))
                Y3.append(float(s[lo[2][0]])*float(lo[2][1]))
            elif s[0] == 'OPAL':
                flag = 1
        f.close()
        # plot 
        idx = args.index(n)
        if choosize == 1:
            c = cm.jet(0, 1)
        else:
            c = cm.jet(float(idx)/(choosize - 1), 1)
        ax1.plot(X[2:], Y1[2:], label=simlabel, color=c)
        ax2.plot(X[2:], Y2[2:], label=simlabel, color=c)
        ax3.plot(X[2:], Y3[2:], label=simlabel, color=c)
        pb.render(int(np.floor(idx / float(choosize) * 100)), 
                  'plotting curves... %s/%s' % (idx + 1, choosize) + suf)
    # set other fig parameters
    lim = None
    ax1.set(xlim=(-0.02, lim))
    ax2.set(xlim=(-0.02, lim))
    ax3.set(xlim=(-0.02, lim))
    ax1.legend(loc='upper left', bbox_to_anchor=(1.02, 1), fancybox=True,
               prop={'size': 8}, shadow=True)
    if save:
        pb.render(99, 'saving plots...' + suf)
        fig.savefig(figname + '.pdf')
    pb.render(100, 'done!')


def plotComp(args, id, zpos, fig=None, ax=None, pb=None):
    options = ['emit_x', 'rms_x', 'energy', 'dE']
    # set progress bar
    suf = "\ncomparison plotting..."
    if not pb:
        pb = ProgressBar(color='blue')
    # read the settings file
    pb.render(0, 'reading plot settings...' + suf)
    try:
        fset = file('ssettings.json')
        settings = json.load(fset)
        fset.close()
        try:
            options = settings['coplot']
            try:
                lo = [statdict[options[0]], statdict[options[1]], \
                      statdict[options[2]], statdict[options[3]]]
            except IndexError:
                pb.render(0, 'settings file format error, using default settings...' + suf)
                options = ['emit_x', 'rms_x', 'energy', 'dE']
                lo = [statdict[options[0]], statdict[options[1]], \
                      statdict[options[2]], statdict[options[3]]]
            except KeyError:
                pb.render(0, "some parameters in settings file don't exist in\
                          statdict, using default settings..." + suf)
                options = ['emit_x', 'rms_x', 'energy', 'dE']
                lo = [statdict[options[0]], statdict[options[1]], \
                      statdict[options[2]], statdict[options[3]]]
        except KeyError:
            pb.render(0, "no settings for coplot in settings file, using\
                      default settings..." + suf)
            lo = [statdict[options[0]], statdict[options[1]], \
                  statdict[options[2]], statdict[options[3]]]
    except IOError:
        pb.render(0, 'no settings file, using default settings...' + suf)
        lo = [statdict[options[0]], statdict[options[1]], \
              statdict[options[2]], statdict[options[3]]]
    # set figure properties
    figname = str(id) + '=[' +  ','.join(args) + ']'
    if not ax:
        if zpos:
            figname = 'CO_zpos=' + zpos + '_id' + figname
        else:
            figname = 'CO_zpos=END_id' + figname
        fig = plt.figure(figsize=(16,10))
        fig.canvas.set_window_title(figname)
        fig.set_label(figname)
        fig.suptitle('COMPARISONS', fontsize=14,
                     fontweight='bold')
        fig.subplots_adjust(left=0.08, right=0.80, top=0.92, bottom=0.07)
        ax = []
        ax.append(fig.add_subplot(221))
        ax.append(fig.add_subplot(222))
        ax.append(fig.add_subplot(223))
        ax.append(fig.add_subplot(224))
        for i in range(4):
            ax[i].set(xlabel='z (m)', ylabel='%s (%s)' % (options[i], lo[i][2]))
            ax[i].grid(True)
    else:
        figname = fig.get_label() + '_id' + figname
        fig.canvas.set_window_title(figname)
        fig.set_label(figname)
    # grab simulation file list from the sim-root directory
    pb.render(0, 'generating scanmap...' + suf)
    simfolder, var, scanrange, scanmap = genScanMap(id)
    if not simfolder:
        pb.render(100, 'done!')
        return fig, ax
    # choose the results we care about
    choose = []
    xaxis = []
    for i in range(len(var)):
        if i < len(args):
            sl = getSlice(args[i])
            if not isinstance(sl, int):
                if not xaxis:
                    choose.append(sl)
                else:
                    choose.append(0)
                xaxis.append(i)
            else:
                choose.append(sl)
        else:
            choose.append(0)
    # generate the chosen simfolders map and list
    choose = tuple(choose)
    choomap = scanmap[choose]
    choolist = choomap.reshape(choomap.size, )
    # travel all the chosen results 
    paras = []
    for n in choolist:
        filename = os.path.join(spParams['home'], simfolder, n,
                                spParams['name']+'.stat') 
        # grab data from simulation files
        try:
            f = file(filename)
        except IOError:
            continue
        flag = 0
        X= []
        Y1 = []
        Y2 = []
        Y3 = []
        Y4 = []
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            s = line.split()
            if flag:
                X.append(float(s[1]))
                Y1.append(float(s[lo[0][0]])*float(lo[0][1]))
                Y2.append(float(s[lo[1][0]])*float(lo[1][1]))
                Y3.append(float(s[lo[2][0]])*float(lo[2][1]))
                Y4.append(float(s[lo[3][0]])*float(lo[3][1]))
            elif s[0] == 'OPAL':
                flag = 1
        f.close()
        # get the parameters at position z
        if zpos:
            zidx = min(range(len(X)), key=lambda i:
                       abs(X[i]-float(zpos)))
        else:
            zidx = -1
        paras.append([Y1[zidx], Y2[zidx], Y3[zidx], Y4[zidx]])
        idx = np.where(choolist==n)[0][0]
        pb.render(int(np.floor(idx / float(choomap.size) * 100)), 
                  'grabbing points... %s/%s' % (idx + 1, choomap.size) + suf)
    # prepare for X, Y axis
    pb.render(99, 'preparing coordinate...' + suf)
    ix = xaxis[0]
    X = np.array(scanrange[ix][choose[ix]])
    xl = var[ix]
    paras = zip(*paras)
    # plot comparisons
    simlabel = genCompLabel(simfolder, choolist[0], xaxis[0])
    for i in range(4):
        ax[i].plot(X, paras[i], label=simlabel)
    # set other fig parameters
    for axis in ax:
        axis.set(xlabel=xl)
    ax[1].legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox= True,
               prop={'size': 10}, shadow=True)
    #fig.tight_layout()
    pb.render(100, 'done!')
    return fig, ax


def plotSim2D(args, id, save, pb=None):
    options = ['emit_x', 'rms_x', 'rms_s']
    # set progress bar
    suf = '\n2d plotting...'
    if not pb:
        pb = ProgressBar(color='blue')
    # read the settings file
    pb.render(0, 'reading plot settings...' + suf)
    try:
        fset = file('ssettings.json')
        settings = json.load(fset)
        fset.close()
        try:
            options = settings['2dplot']
        except KeyError:
            pb.render(0, "no settings for 2dplot in settings file, using\
                      default settings..." + suf)
    except IOError:
        pb.render(0, 'no settings file, using default settings...' + suf)
    # set figure properties
    figname = '2D_id' + str(id) + '=[' +  ','.join(args) + ']'
    fig = plt.figure(num=figname, figsize=(12,12))
    ax1 = fig.add_axes([0.09, 0.52, 0.65, 0.42])
    ax2 = fig.add_axes([0.09, 0.05, 0.65, 0.42])    
    # ax1 = fig.add_axes([0.09, 0.69, 0.65, 0.27])
    # ax2 = fig.add_axes([0.09, 0.37, 0.65, 0.27])
    # ax3 = fig.add_axes([0.09, 0.05, 0.65, 0.27])
    ax1.set_yscale('log')
    ax2.set_yscale('log')
    #ax3.set_yscale('log')
    try:
        lo = [statdict[options[0]], statdict[options[1]], statdict[options[2]]]
    except IndexError:
        pb.render(0, 'settings file format error, using default settings...' + suf)
        options = ['emit_x', 'rms_x', 'rms_s']
        lo = [statdict[options[0]], statdict[options[1]], statdict[options[2]]]
    except KeyError:
        pb.render(0, "some parameters in settings file don't exist in\
                  statdict, using default settings..." + suf)
        options = ['emit_x', 'rms_x', 'rms_s']
        lo = [statdict[options[0]], statdict[options[1]], statdict[options[2]]]
    fig.suptitle('%s & %s' % tuple(options[:2]), fontsize=14,
                 fontweight='bold')
    ax1.set(xlabel='z (m)', ylabel='%s (%s)' % (options[0], lo[0][2]))
    ax2.set(xlabel='z (m)', ylabel='%s (%s)' % (options[1], lo[1][2]))
    # ax3.set(xlabel='z (m)', ylabel='%s (%s)' % (options[2], lo[2][2]))
    # ax3.set(xlabel='z (m)', ylabel='dE_x (MeV)')
    ax1.grid(True)
    ax2.grid(True)
    # ax3.grid(True)
    # grab simulation file list from the sim-root directory
    pb.render(0, 'generating scanmap...' + suf)
    simfolder, var, _r, scanmap = genScanMap(id)
    if not simfolder:
        pb.render(100, 'done!')
        return
    # choose the results we care about
    choose = []
    for i in range(len(var)):
        if i < len(args):
            sl = getSlice(args[i])
            choose.append(sl)
        else:
            choose.append(0)
    # generate the chosen simfolders list
    choose = tuple(choose)
    try:
        choosize = scanmap[choose].size
    except IndexError:
        pb.render(100, 'done!')
        return
    choomap = scanmap[choose].reshape(choosize, )
    #lim = []
    # travel all the chosen results 
    for n in choomap:
        filename = os.path.join(spParams['home'], simfolder, n,
                                spParams['name']+'.stat') 
        simlabel = genSimLabel(simfolder, n)
        # grab data from simulation files
        try:
            f = file(filename)
        except IOError:
            continue
        flag = 0
        X= []
        Y1 = []
        Y2 = []
        Y3 = []
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            s = line.split()
            if flag:
                X.append(float(s[1]))
                Y1.append(float(s[lo[0][0]])*float(lo[0][1]))
                Y2.append(float(s[lo[1][0]])*float(lo[1][1]))
                Y3.append(float(s[lo[2][0]])*float(lo[2][1]))
            elif s[0] == 'OPAL':
                flag = 1
        f.close()
        # plot 
        idx = np.where(choomap==n)[0][0]
        if choosize == 1:
            c = cm.jet(0, 1)
        else:
            c = cm.jet(float(idx)/(choosize - 1), 1)
        ax1.plot(X[2:], Y1[2:], label=simlabel, color=c)
        ax2.plot(X[2:], Y2[2:], label=simlabel, color=c)
        # ax3.plot(X[2:], Y3[2:], label=simlabel, color=c)
        idx = np.where(choomap==n)[0][0]
        pb.render(int(np.floor(idx / float(choosize) * 100)), 
                  'plotting curves... %s/%s' % (idx + 1, choosize) + suf)
    # set other fig parameters
    lim = None
    ax1.set(xlim=(-0.02, lim))
    ax2.set(xlim=(-0.02, lim))
    # ax3.set(xlim=(-0.02, lim))
    ax1.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fancybox=True,
               prop={'size': 10}, shadow=True)
    if save:
        pb.render(99, 'saving plots...' + suf)
        fig.savefig(figname + '.pdf')
    pb.render(100, 'done!')


def plotSim3D(args, id, save, js, pb=None):
    # set figure properties
    figname = '3D_id' + str(id) + '=[' +  ','.join(args) + ']'
    fig = plt.figure(figname, figsize=(18, 8))
    fig.suptitle('Ferrario Point Trace', fontsize=14, fontweight='bold')
    ax = fig.add_subplot(121, projection='3d')
    ax2 = fig.add_subplot(122)
    plt.subplots_adjust(left=0.03, right=0.92, top=0.92, bottom=0.08, wspace=0.3)
    # set progress bar
    suf = '\n3d plotting...'
    if not pb:
        pb = ProgressBar(color='blue')
    # generate scanmap 
    pb.render(0, 'generating scanmap...' + suf)
    simfolder, var, scanrange, scanmap = genScanMap(id)
    if not simfolder:
        pb.render(100, 'done!')
        return
    # choose the results we care about
    choose = []
    xyaxis = []
    for i in range(len(var)):
        if i < len(args):
            sl = getSlice(args[i])
            if not isinstance(sl, int):
                xyaxis.append(i)
            choose.append(sl)
        else:
            choose.append(0)
    # generate the chosen simfolders map and list
    choose = tuple(choose)
    choomap = scanmap[choose]
    choolist = choomap.reshape(choomap.size, )
    # travel all the chosen results to grab peak from simulation files
    EMIMAX = [] 
    SIGMIX = []
    for p in choolist:
        filename = os.path.join(spParams['home'], simfolder, p,
                                spParams['name']+'.stat') 
        try:
            f = file(filename)
        except IOError:
            continue
        flag = 0
        POSZ = []
        EMIX = []
        SIGX = []
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            s = line.split()
            if flag:
                POSZ.append(float(s[1]))
                EMIX.append(float(s[11]))
                SIGX.append(float(s[5]))
            elif s[0] == 'OPAL':
                flag = 1
        f.close()
        EMIPEAKS = getPeaks(POSZ, EMIX)[0]
        SIGPEAKS = getPeaks(POSZ, SIGX)[1]
        if EMIPEAKS:
            EMIMAX.append(EMIPEAKS[-1][0])
        else:
            EMIMAX.append(0)
        if SIGPEAKS:
            SIGMIX.append(SIGPEAKS[-1][0])
        else:
            SIGMIX.append(0)
        idx = np.where(choolist==p)[0][0]
        tot = len(choolist)
        pb.render(int(np.floor(idx / float(tot) * 100)), 'grabbing peaks... %s/%s' % 
                  (idx + 1, tot) + suf)
    # reshape EMIMAX and SIGMIN
    pb.render(99, 'preparing coordinate...' + suf)
    EMIMAX = np.array(EMIMAX)
    SIGMIX = np.array(SIGMIX)
    EMIMAX.shape = choomap.shape
    SIGMIX.shape = choomap.shape
    # generate x, y axis
    ix = xyaxis[0]
    iy = xyaxis[1]
    X = np.array(scanrange[ix][choose[ix]])
    Y = np.array(scanrange[iy][choose[iy]])
    xl = var[ix]
    yl = var[iy]
    # 2D plot to show the cross line of the 2 surfaces
    def getLambda(p1, p2):
        return p1 / float(p1 - p2) 
    def getPoint(lamb, x1, x2):
        return (1 - lamb) * x1 + lamb * x2
    DIFF = SIGMIX - EMIMAX
    crossx = []
    crossy = []
    crossz = []
    # get cross points from x view point
    for i in range(len(X)):
        arr = DIFF[i, :]
        cro = [j for j in range(len(arr) - 1) if (arr[j] * arr[j+1] <= 0) and
               SIGMIX[i, j] and SIGMIX[i, j+1] and EMIMAX[i, j] and 
               EMIMAX[i, j+1] and (abs(EMIMAX[i, j] - EMIMAX[i, j+1]) < 1)]
        if cro:
            for pos in cro:
                lamb = getLambda(arr[pos], arr[pos + 1])
                ypos = getPoint(lamb, Y[pos], Y[pos + 1])
                fpos = getPoint(lamb, EMIMAX[i, pos], EMIMAX[i, pos + 1])
                crossx.append(X[i])
                crossy.append(ypos)
                crossz.append(fpos)
    # get cross points from y view point
    for i in range(len(Y)):
        arr = DIFF[:, i]
        cro = [j for j in range(len(arr) - 1) if (arr[j] * arr[j+1] <= 0) and
               SIGMIX[j, i] and SIGMIX[j+1, i] and EMIMAX[j, i]
               and EMIMAX[j+1, i] and (abs(EMIMAX[j, i] - EMIMAX[j+1, i]) < 1)]
        if cro:
            for pos in cro:
                lamb = getLambda(arr[pos], arr[pos + 1])
                xpos = getPoint(lamb, X[pos], X[pos + 1])
                fpos = getPoint(lamb, EMIMAX[pos, i], EMIMAX[pos + 1, i])
                crossx.append(xpos)
                crossy.append(Y[i])
                crossz.append(fpos)
    [crossx, crossy, crossz] = zip(*sorted(zip(crossx, crossy, crossz), 
                                           key=lambda tup: tup[0]))
    ax.plot(crossx, crossy, color='g', marker='^')
    # write ferrario point list
    if js:
        pb.render(99, 'writing ferrario points...' + suf)
        fname = '_id' + str(id) + '=[' +  ','.join(args) + ']'
        f = file('ferrario_point' + fname + '.json', 'w')
        flist = OrderedDict()
        flist['title'] = 'Ferrario Point List'
        flist['variables'] = [xl, yl, 'ZPOS']
        flist['point list'] = zip(crossx, crossy, crossz)
        f.write(json.dumps(flist, sort_keys=False, indent=4, separators=(',', ': '))) 
        f.close()
    # 3D plot
    Y, X = np.meshgrid(Y, X)
    ax.plot_surface(X, Y, EMIMAX, rstride=1, cstride=1, color='b', alpha=0.5)
    ax.plot_surface(X, Y, SIGMIX, rstride=1, cstride=1, color='r', alpha=0.5)
    label0 = 'MATCH'
    label1 = 'EMIMAX'
    label2 = 'SIGMIX'
    p0 = plt.Line2D([0], [0], color='g', marker='^')
    p1 = plt.Rectangle((0, 0), 1, 1, fc="b", alpha=0.5)
    p2 = plt.Rectangle((0, 0), 1, 1, fc="r", alpha=0.5)
    sthing = [p1, p2, p0]
    slabel = [label1, label2, label0]
    ax.set(xlabel=xl, ylabel=yl, zlabel='SPOS (m)') 
    ax.legend(sthing, slabel, loc='upper left', bbox_to_anchor=(1, 1), fancybox= True,
              prop={'size': 12}, shadow=True)
    # plot another 2D relation fig
    ax2.plot(crossx, crossy, color='g', marker='^', label='MATCH')
    ax2.set(xlabel=xl, ylabel=yl)
    ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), fancybox= True,
               prop={'size': 12}, shadow=True)
    ax2.grid() 
    if save:
        pb.render(99, 'saving plots...' + suf)
        fig.savefig(figname + '.pdf')
    pb.render(100, 'done!')


def main():
    # user friendly command line arguments manual
    intro = """hello there, I'm sscout, a small
               code equiped some useful features to
               help you dealing with the .stat file that generated by OPAL."""
    parser = argparse.ArgumentParser(description=intro)
    parser.add_argument('-v', '--version', action='version', version='sscout 1.1')
    parser.add_argument('id', nargs='*', help="""every simfolder has an id (you
                        will know when you run this code without any arguments),
                        so we specify the simfolders we care by specified the
                        id of them. 'id' should be a list of slice.
                        if not specified, the default value is ':'""")
    parser.add_argument('-bu', '--backup', action='store_true', help="""back up
                        the .stat files in simfolders 
                        which are specified by 'id' argument""")
    parser.add_argument('-ck', '--check', action='store_true', help="""check out
                        if the .stat files exist in simfolders 
                        which are specified by 'id' argument""")
    parser.add_argument('-ls', '--list', action='store_true', help="""list the 
                        folder name of every subfolder in simfolders which are specified
                        by 'id' argument""")
    parser.add_argument('-ge', '--geneplot', action='append', nargs='+',
                        dest='plotgene', metavar='arg', help="""
                        draw 2D plot for the rerun generation simulations""")
    parser.add_argument('-2d', '--2dplot', action='append', nargs='+',
                        dest='plot2d', 
                        metavar='arg', help="""
                        draw 2D plots of specified simulations in target simfolder. 
                        it will show the emittance, beamsize, energy
                        spread, etc vs. longitudinal position on the plots. 
                        notice that the target simfolder in which we draw 2D plots
                        is not specified by 'id' argument, but by the first
                        argument follows '-2d' commmand, which is an required
                        argument, and must be an integer (not a slice or
                        something). which simulations in that simfolder we will draw
                        are specified by the rest args, which should be some slices.
                        if not specified, the default is '0 ...', that means
                        just plot the first simulation in target simfolder.
                        you can add several '-2d' commands to draw 2D plots in
                        different simfolders, just change the args follow each '-2d'
                        commands""")
    parser.add_argument('-3d', '--3dplot', action='append', nargs='+', 
                        dest='plot3d',
                        metavar='arg', help="""
                        draw 3D plots of specified simulations in target simfolder.
                        it will show the ferrario point trace on the plots. 
                        notice that the target simfolder in which we draw 3D plots
                        is not specified by 'id' argument, but by the first
                        argument follows '-3d' commmand, which is an required
                        arg, and must be an integer (not a slice or
                        something). also notice that you can draw 3D plots only
                        when the target simfolder contains simulation results of
                        scan for at least 2 parameters. 
                        which simulations in that simfolder we will draw
                        are specified by the rest args, which should be some slices.
                        but in case we are plotting 3D plots, only 2 parameters
                        can be treat as variables. so if you have scan 3 or more
                        parameters, you can only specified 2 of them as
                        slice, and the rest as position (integer).
                        if not specified, the default is ': : 0 ...', which
                        means use the first 2 parameters as variables and draw
                        the plots when other parameters take their first value. 
                        you can add several '-3d' commands to draw 3D plots in
                        different simfolders, just change the args follow each '-3d'
                        commands.
                        you can also get a json file which contains list of all 
                        ferrario points in range specified by args follow '-3d', 
                        by adding '-f' or '--fpoint' argument""")
    parser.add_argument('-co', '--coplot', action='append', nargs='+', 
                        dest='plotco', metavar='arg', help="""
                        comparison plots""")
    parser.add_argument('-z', '--zpos', action='store', nargs='+', 
                        dest='zpos', metavar='pos', help="""
                        specify the z position where we draw comparison plots""")
    parser.add_argument('-s', '--save', action='store_true', help="""save
                        all figures generated by argument '-2d' and '-3d' in pdf
                        format""")
    parser.add_argument('-f', '--fpoint', action='store_true', help="""generate
                        json file that contains all ferrario points in ranges
                        that specified by arguments follow '-3d', must be used
                        with '-3d' argument""")
    parser.add_argument('-d', '--detail', action='store_true', help="""show details
                        of the result of '.stat' files check""")
    parser.add_argument('-p', '--showparas', action='store_true', help="""show
                        simulation parameters under root simfolder, in fact it
                        shows the parameters in projname.data""")
    parser.add_argument('-ho', '--home', nargs=1,
                        dest='home', metavar='dir', help="""
                        set simulation home directory, sscout will search for
                        simualtion folders under the specified directory 'dir',
                        if not specified, sscout will set current directory
                        as the simulation root directory.""")
    parser.add_argument('-n', '--name', nargs=1, dest='name',
                        metavar= 'name', help="""
                        set the simulation project name, ffinder will search for
                        the simulation folders of which the name starts with the
                        project name 'name'. If not specified, sscout will try
                        to point out the project name automatically.""")
    # parse command line and get all arguments
    args = parser.parse_args()
    # set init flag
    noarg_flag = 1
    # set sim homedir and name
    if args.home:
        spParams['home'] = args.home[0]
    if args.name:
        spParams['name'] = args.name[0]
    else:
        autoDetectProj()
    # take actions
    #pb = ProgressBar(color='blue')
    pb = ProgressBar(color='black', block='=', width=40)
    id = mergeIDs(args.id)
    if args.list:
        listSimFolders(id)
        noarg_flag = 0
    if args.showparas:
        showSimParas()
        noarg_flag = 0
    if args.backup:
        easyBackup(id, pb)
        noarg_flag = 0
    if args.check:
        check(id, args.detail)
        noarg_flag = 0
    if args.plotgene:
        for arg in args.plotgene:
            plotGene2D(arg[1:], int(arg[0]), args.save, pb)
    if args.plot2d:
        for arg in args.plot2d:
            plotSim2D(arg[1:], int(arg[0]), args.save, pb)
    if args.plot3d:
        for arg in args.plot3d:
            plotSim3D(arg[1:], int(arg[0]), args.save, args.fpoint, pb)
    if args.plotco:
        if args.zpos:
            for z in args.zpos:
                for i, arg in enumerate(args.plotco):
                    if i == 0:
                        fig, ax = plotComp(arg[1:], int(arg[0]), z, pb=pb) 
                    else:
                        plotComp(arg[1:], int(arg[0]), z, fig, ax, pb)
        else:
            for i, arg in enumerate(args.plotco):
                if i == 0:
                    if len(arg) > 1:
                        fig, ax = plotComp(arg[1:], int(arg[0]), args.zpos, pb=pb) 
                    else:
                        fig, ax = plotComp([':',], int(arg[0]), args.zpos, pb=pb) 
                else:
                    plotComp(arg[1:], int(arg[0]), args.zpos, fig, ax, pb)
    if args.plot2d or args.plot3d or args.plotco or args.plotgene:
        plt.show()
    elif noarg_flag and (not args.save) and (not args.fpoint) and\
         (not args.detail) and (not args.zpos):
        showSimInfo(id)
        if not args.id and (not args.home) and (not args.name):
            print render('%(GREEN)s' + "getting help by adding argument '-h'" + '%(NORMAL)s')


if __name__ == '__main__':
    main()


