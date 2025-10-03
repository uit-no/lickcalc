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
        # First, try to read as a regular CSV with headers
        try:
            reader = csv.DictReader(f)
            cols = reader.fieldnames
            loaded_vars = {}
            for col in cols:
                loaded_vars[col] = []
            
            f.seek(0)
            reader = csv.DictReader(f)  # Reset reader after seek
            for row in reader:
                for col in cols:
                    try:
                        loaded_vars[col].append(float(row[col]))
                    except (ValueError, TypeError):
                        pass  # Skip non-numeric values
        except:
            # If that fails, try reading as a simple CSV without headers
            f.seek(0)
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) == 0:
                loaded_vars = {'Column_1': []}
            else:
                # Check if first row looks like headers (contains non-numeric data)
                first_row = rows[0]
                has_headers = False
                try:
                    [float(x) for x in first_row]
                except ValueError:
                    has_headers = True
                
                if has_headers:
                    headers = first_row
                    data_rows = rows[1:]
                else:
                    headers = [f'Column_{i+1}' for i in range(len(first_row))]
                    data_rows = rows
                
                loaded_vars = {header: [] for header in headers}
                
                for row in data_rows:
                    for i, value in enumerate(row):
                        if i < len(headers):
                            try:
                                loaded_vars[headers[i]].append(float(value))
                            except (ValueError, TypeError):
                                pass  # Skip non-numeric values
    
    # Remove empty columns
    loaded_vars = {k: v for k, v in loaded_vars.items() if len(v) > 0}
    
    # If no columns have data, create a dummy column
    if not loaded_vars:
        loaded_vars = {'No_Data': []}
    
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

