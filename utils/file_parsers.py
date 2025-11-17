"""
File parsing utilities for lickcalc webapp.
Functions to parse different lick data file formats (MED, CSV, DD).
"""
import os
import numpy as np
import string
import re
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

def parse_med_arraystyle(f):
    """Parser for Med-PC format arrays, i.e. not column-based.
    
    Args:
        f: File-like object (e.g., StringIO) or file path string
    """
    # Handle both file paths and file-like objects
    if isinstance(f, str):
        with open(f, 'r') as file:
            lines = file.readlines()
    else:
        # f is already a file-like object (StringIO)
        f.seek(0)  # Reset to beginning
        lines = f.readlines()
    
    arrays = {}
    current_array = None
    
    for line in lines:
        # Check for array label (e.g., "L:" or "R:")
        if re.match(r'^[A-Z]:$', line.strip()):
            current_array = line.strip()[0]  # Get just the letter
            arrays[current_array] = []
        # Check for data lines (start with spaces and numbers)
        elif current_array and re.match(r'^\s+\d+:', line):
            # Extract all decimal numbers from the line
            numbers = re.findall(r'\d+\.\d+', line)
            arrays[current_array].extend([float(n) for n in numbers])
    
    # Remove trailing zeros
    for key in arrays:
        while arrays[key] and arrays[key][-1] == 0.0:
            arrays[key].pop()
    
    data_array = vars2dict(arrays)
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

def parse_ohrbets(f):
    codes, ts = [], []

    # Handle both file paths and file-like objects
    if isinstance(f, (str, bytes, os.PathLike)):
        with open(f, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) > 0:
                    row = row[0].split(" ")
                    # Keep codes as strings for consistent handling; sort numerically later when possible
                    codes.append(str(row[0]).strip())
                    ts.append(int(row[1]) / 1000)
    else:
        f.seek(0)
        reader = csv.reader(f)
        for row in reader:
            if len(row) > 0:
                row = row[0].split(" ")
                codes.append(str(row[0]).strip())
                ts.append(int(row[1]) / 1000)

    df = pd.DataFrame({"code": codes, "ts": ts})

    # Define a sort key that prefers numeric codes ordered by integer value,
    # with non-numeric codes sorted lexicographically after numeric ones.
    def _code_sort_key(k):
        s = str(k)
        return (0, int(s)) if s.isdigit() else (1, s)

    sorted_codes = sorted(df.code.unique().tolist(), key=_code_sort_key)

    code_dict = {}
    for code in sorted_codes:
        code_dict[code] = df.loc[df["code"] == code, "ts"].values

    data_array = vars2dict(code_dict)

    return data_array

def find_presentation_line(filepath, str2search="PRESENTATION"):
    with open(filepath, newline='') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if row[0] == str2search:
                return i
            
def get_ilis_from_file(filepath, datastart=None):

    return (
        pd
        .read_csv(filepath, skiprows=datastart+2, header=None)
        .astype(np.int32)
        .iloc[0,:]
        .T
        .reset_index(drop=True)
        .values
    )

def parse_lsfile(filepath):

    datastart = find_presentation_line(filepath)

    df = get_ilis_from_file(filepath, datastart=datastart)
    solution = pd.read_csv(filepath, skiprows=datastart, nrows=1)["SOLUTION"].values[0].strip()
    latency = pd.read_csv(filepath, skiprows=datastart, nrows=1)[" Latency"].values[0]

    all_ilis = np.array([latency] + df.tolist())
    licks = np.cumsum(all_ilis)
    licks_in_seconds = licks / 1000

    data_array = {}
    data_array[solution] = licks_in_seconds

    return vars2dict(data_array)

def vars2dict(loaded_vars):
         
    data_array = {}
    for v in loaded_vars:
        df = pd.DataFrame(loaded_vars[v], columns=['licks'])
        data_array[v] = df.to_json(orient='split')
        
    return data_array

