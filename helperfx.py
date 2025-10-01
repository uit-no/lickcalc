# -*- coding: utf-8 -*-
"""
Created on Tue Jul  6 20:18:49 2021

@author: jmc010
"""
import numpy as np
import string
import scipy.optimize as opt
import scipy.stats as stats
import pandas as pd
import json
import csv
import datetime
from trompy import tstamp_to_tdate


def parse_medfile(f):
    
    sessionToExtract=1

    f.seek(0)
    filerows = f.readlines()[8:]
    datarows = [isnumeric(x) for x in filerows]
    matches = [i for i,x in enumerate(datarows) if x == 0.3]
    if sessionToExtract > len(matches):
        print('Session ' + str(sessionToExtract) + ' does not exist.')
    
    varstart = matches[sessionToExtract - 1]    
    loaded_vars = {}
   
    k = int(varstart + 27)
    for i in range(26):
        medvarsN = int(datarows[varstart + i + 1])
        if medvarsN > 1:
            loaded_vars[string.ascii_uppercase[i]] = datarows[k:k + int(medvarsN)]
        k = k + medvarsN

    for val in loaded_vars.values():
        val.pop(0)

    data_array = vars2dict(loaded_vars)
                
    return data_array

def isnumeric(s):
    """ Converts strings into numbers (floats) """
    try:
        x = float(s)
        return x
    except ValueError:
        return float('nan')

def parse_csvfile(f):                      
    
    with f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames
        loaded_vars = {}
        for col in cols:
            loaded_vars[col] = []
            f.seek(0)
            for row in reader:
                try:
                    loaded_vars[col].append(float(row[col]))
                except:
                    pass 
    
    data_array = vars2dict(loaded_vars)
    
    return data_array

def parse_ddfile(f):

    header = 6
    vals = f.readlines()[header:]
    f.close()
    ts = [tstamp_to_tdate(val, '%H:%M:%S.%f\n') for val in vals]
    delta = [t-ts[idx-1] for idx, t in enumerate(ts[1:])]
    delta_array = np.array([d.total_seconds() for d in delta])
    if min(delta_array) < 0: #tests if timestamps span midnight
        dayadvance = np.where(delta_array < 0)[0][0]
        ts = ts[:dayadvance+1] + [t + datetime.timedelta(days=1) for t in ts[dayadvance+1:]]
    t0=ts[0]
    loaded_vars = {'t': [(t - t0).total_seconds() for t in ts]}
    
    data_array = vars2dict(loaded_vars)
    
    return data_array

def vars2dict(loaded_vars):
         
    data_array = {}
    for v in loaded_vars:
        df = pd.DataFrame(loaded_vars[v], columns=['licks'])
        data_array[v] = df.to_json(orient='split')
        
    return data_array

def lickCalc(licks, offset = [], burstThreshold = 0.5, runThreshold = 10,
             ignorelongilis=True, longlickThreshold=0.3, minburstlength=1,
             binsize=60, histDensity = False):
    """
    Calcuates various parameters for a train of licking data including bursting 
    parameters and returns as a dictionary.

    Parameters
    ----------
    licks : List or 1D array
        Timestamps of licks (onsets). Expects in seconds. If given in ms then other
        parameters should be changed, e.g. burstThreshold.
    offset : List or 1D array, optional
        Timestamps of lick offsets. The default is [].
    burstThreshold : Float, optional
        Interlick threshold (in seconds) for defining bursts. See Naneix et al (2019) for more info.
        https://doi.org/10.1016/j.neuroscience.2019.10.036 The default is 0.5.
    runThreshold : Float or Int, optional
        Number of seconds separating runs of licks. The default is 10.
    ignorelongilis : Boolean, optional
        Removes ILIs over burstThreshold from calcuations. Useful for calculating
        intraburst frequency. The default is True.
    longlickThreshold : Float, optional
        Threshold (in seconds) for long licks. The default is 0.3.
    minburstlength : Int, optional
        Minimum number of licks to be considered a burst. Common values are either 1 or 3. The default is 1.
    binsize : Int or Float, optional
        Size of bins for constructing histogram. The default is 60.
    histDensity : Boolean, optional
        Converts histogram into a density plot rather than absolute. The default is False.

    Returns
    -------
    lickData : Dictionary with the following keys - 
        'licklength' - list of lick lengths (only available if offset times given).
        'longlicks' - list of licks that are greater than longlickThreshold
        'licks' - list of lick onset times
        'ilis' - list of interlick intervals
        'freq' - mean frequency (in Hz) of intraburst licking
        'total' - number of licks
        'bStart' - list of timestamps of licks that start a burst
        'bInd' - list of indices of licks that start a burst
        'bEnd' - list of indices of licks that end a burst
        'bLicks' - list with numbers of licks in each burst
        'bTime' - Array of Floats with time (in seconds) of each burst
        'bMean' - Float, mean of all bursts
        'bMean-first3' - Float, mean of first three bursts
        'IBIs' - List of interburst intervals
        'rStart' - List of start times for all runs
        'rInd' - List of lick indices where runs start
        'rEnd' - List of end times for all runs
        'rLicks' - List of numbers of licks per run
        'rTime' - Array of floats with time (in seconds) of each run
        'rNum' - Int, number of runs
        'weib_alpha' - Float, alpha parameter with fitted Weibull function
        'weib_beta' - Float, beta parameter of Weibull
        'weib_rsq' - Float, rsq of Weibull fit
        'burstprob' - List with xdata and ydata of cumulative burst probability
        'hist' - Histogram of licks over time
        
    """
    # makes dictionary of data relating to licks and bursts
    if type(licks) != np.ndarray or type(offset) != np.ndarray:
        try:
            licks = np.array(licks)
            offset = np.array(offset)
        except:
            print('Licks and offsets need to be arrays and unable to easily convert.')
            return
    
    lickData = {}

    if len(offset) > 0:
        licks = licks[:len(offset)]
        lickData['licklength'] = offset - licks
        if min(lickData['licklength']) < 0:
            print("Some offsets precede onsets. Not doing lick length analysis.")
            lickData['licklength'] = []
            lickData['longlicks'] = []
        else:
            lickData['longlicks'] = [x for x in lickData['licklength'] if x > longlickThreshold]
    else:
        lickData['licklength'] = []
        lickData['longlicks'] = []

    lickData['licks'] = np.concatenate([[0], licks])
    lickData['ilis'] = np.diff(lickData['licks'])
    if ignorelongilis:
        lickData['ilis'] = [x for x in lickData['ilis'] if x < burstThreshold]

    lickData['freq'] = 1/np.mean([x for x in lickData['ilis'] if x < burstThreshold])
    lickData['total'] = len(licks)
    
    # Calculates start, end, number of licks and time for each BURST 
    lickData['bStart'] = [val for i, val in enumerate(lickData['licks']) if (val - lickData['licks'][i-1] > burstThreshold)]  
    lickData['bInd'] = [i for i, val in enumerate(lickData['licks']) if (val - lickData['licks'][i-1] > burstThreshold)]
    lickData['bEnd'] = [lickData['licks'][i-1] for i in lickData['bInd'][1:]]
    lickData['bEnd'].append(lickData['licks'][-1])

    lickData['bLicks'] = np.diff(lickData['bInd'] + [len(lickData['licks'])])
    
    # calculates which bursts are above the minimum threshold
    inds = [i for i, val in enumerate(lickData['bLicks']) if val>minburstlength-1]
    
    lickData['bLicks'] = removeshortbursts(lickData['bLicks'], inds)
    lickData['bStart'] = removeshortbursts(lickData['bStart'], inds)
    lickData['bEnd'] = removeshortbursts(lickData['bEnd'], inds)
      
    lickData['bTime'] = np.subtract(lickData['bEnd'], lickData['bStart'])
    lickData['bNum'] = len(lickData['bStart'])
    if lickData['bNum'] > 0:
        lickData['bMean'] = np.nanmean(lickData['bLicks'])
        lickData['bMean-first3'] = np.nanmean(lickData['bLicks'][:3])
    else:
        lickData['bMean'] = 0
        lickData['bMean-first3'] = 0
    
    lickData['IBIs'] = []
    for bEnd in lickData['bEnd'][:-1]:
        nextlick = [lick for lick in licks if lick > bEnd][0]
        lickData['IBIs'].append(nextlick - bEnd)
        
    # Calculates start, end, number of licks and time for each RUN
    lickData['rStart'] = [val for i, val in enumerate(lickData['licks']) if (val - lickData['licks'][i-1] > runThreshold)]  
    lickData['rInd'] = [i for i, val in enumerate(lickData['licks']) if (val - lickData['licks'][i-1] > runThreshold)]
    lickData['rEnd'] = [lickData['licks'][i-1] for i in lickData['rInd'][1:]]
    lickData['rEnd'].append(lickData['licks'][-1])

    lickData['rLicks'] = np.diff(lickData['rInd'] + [len(lickData['licks'])])    
    lickData['rTime'] = np.subtract(lickData['rEnd'], lickData['rStart'])
    lickData['rNum'] = len(lickData['rStart'])

    try:
        xdata, ydata = calculate_burst_prob(lickData['bLicks'])
        try:
            lickData['weib_alpha'], lickData['weib_beta'], lickData['weib_rsq'] = fit_weibull(xdata, ydata)
        except RuntimeError:
            print('Optimal fit parameters not found')
            lickData['weib_alpha'], lickData['weib_beta'], lickData['weib_rsq'] = [0, 0, 0]
        except TypeError:
            print('Optimal fit parameters not found')
            lickData['weib_alpha'], lickData['weib_beta'], lickData['weib_rsq'] = [0, 0, 0]
            
        lickData['burstprob']=[xdata, ydata]
    except ValueError:
        print('Could not calculate burst probability')
        lickData['weib_alpha'], lickData['weib_beta'], lickData['weib_rsq'] = [0, 0, 0]
        lickData['burstprob']=[[0], [0]]
    try:
        lickData['hist'] = np.histogram(lickData['licks'][1:], 
                                    range=(0, 3600), bins=int((3600/binsize)),
                                          density=histDensity)[0]
    except TypeError:
        print('Problem making histograms of lick data')
        
    return lickData

def removeshortbursts(data, inds):
    """
    Removes bursts that do not meet minimum burst criteria.

    Parameters
    ----------
    data : List
        Data with parameters of individual bursts.
    inds : List
        Indices of bursts to be removed.

    Returns
    -------
    data : List
        Burst parameters with those that did not meet criterion removed.

    """
    data = [data[i] for i in inds]
    return data

def calculate_burst_prob(bursts):
    """
    Calculates cumulative burst probability as in seminal Davis paper
    DOI: 10.1152/ajpregu.1996.270.4.R793

    Parameters
    ----------
    bursts : List
        List with lengths of bursts.

    Returns
    -------
    x : List
        x values (bin sizes).
    y : List
        y values of cumulative burst probability.

    """
    bins = np.arange(min(bursts), max(bursts))
    hist=np.histogram(bursts, bins=bins, density=True)
    cumsum=np.cumsum(hist[0])

    x = hist[1][1:]
    y = [1-val for val in cumsum]
    
    return x, y

def weib_davis(x, alpha, beta):
    '''Weibull function as used in Davis (1998) DOI: 10.1152/ajpregu.1996.270.4.R793'''
    return (np.exp(-(alpha*x)**beta))

def fit_weibull(xdata, ydata):
    '''Fits Weibull function to xdata and ydata and returns fit parameters.'''
    x0=np.array([0.1, 1])
    fit=opt.curve_fit(weib_davis, xdata, ydata, x0)
    alpha=fit[0][0]
    beta=fit[0][1]
    slope, intercept, r_value, p_value, std_err = stats.linregress(ydata, weib_davis(xdata, alpha, beta))
    r_squared=r_value**2
    
    return alpha, beta, r_squared