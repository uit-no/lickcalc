"""
File parsing utilities for lickcalc webapp.
Functions to parse different lick data file formats (MED, CSV, DD).
"""
import numpy as np
import string
import pandas as pd
import csv
import datetime
from trompy import tstamp_to_tdate


def parse_medfile(f):
    
    session_to_extract = 1

    f.seek(0)
    filerows = f.readlines()[8:]
    datarows = [isnumeric(x) for x in filerows]
    matches = [i for i, x in enumerate(datarows) if x == 0.3]
    if session_to_extract > len(matches):
        raise ValueError(f'Session {session_to_extract} does not exist.')
    
    varstart = matches[session_to_extract - 1]    
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
        # Read all rows first to determine if we have headers
        f.seek(0)
        reader = csv.reader(f)
        rows = list(reader)
        
        if len(rows) == 0:
            loaded_vars = {'Col. 1': []}
        else:
            # Check if first row looks like headers (contains non-numeric data)
            first_row = rows[0]
            has_headers = False
            
            # Check if first row contains timestamp-like data (floats)
            try:
                # Try to convert all values in first row to float
                numeric_count = 0
                total_count = 0
                
                for value in first_row:
                    # Strip whitespace and check if it's a valid number
                    clean_value = str(value).strip()
                    if clean_value:  # Not empty
                        total_count += 1
                        try:
                            float(clean_value)  # This will raise ValueError if not a number
                            numeric_count += 1
                        except ValueError:
                            pass
                
                # If all non-empty values in first row are numeric, treat as data
                # If any non-empty value is non-numeric, treat as headers
                if total_count > 0 and numeric_count == total_count:
                    has_headers = False
                else:
                    has_headers = True
                    
            except Exception:
                # If any error occurs, assume headers for safety
                has_headers = True
            
            if has_headers:
                headers = first_row
                data_rows = rows[1:]
            else:
                # No headers detected, create generic column names
                headers = [f'Col. {i+1}' for i in range(len(first_row))]
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
        loaded_vars = {'Col. 1': []}
    
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

def parse_kmfile(f, header=9):

    df = pd.read_csv(f,
                    skiprows=header,
                    header=None,
                    names=["row", "timestamp", "input", "eventcode", "event", "empty1", "empty2"]
                    )
    
    loaded_vars = {}

    for event in df.event.unique():
        tmp = df.query("event == @event").timestamp.values
        loaded_vars[event] = tmp
        
    data_array = vars2dict(loaded_vars)
    
    return data_array

def vars2dict(loaded_vars):
         
    data_array = {}
    for v in loaded_vars:
        df = pd.DataFrame(loaded_vars[v], columns=['licks'])
        data_array[v] = df.to_json(orient='split')
        
    return data_array

