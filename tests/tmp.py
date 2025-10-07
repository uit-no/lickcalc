# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5 19:40:56 2021

@author: jmc010
"""
import pandas as pd
import numpy as np

import trompy as tp

import plotly.express as px
import json

from helperfx import parse_medfile
from trompy import lickcalc

file = "D:\\Test Data\\medfiles\\!2017-07-28_07h43m.Subject pcf1.07"
# file = "D:\\Test Data\\medfiles\\!2018-10-16_11h33m.Subject IPP2.16"

licks = tp.medfilereader_licks(file)

df = pd.DataFrame(np.array([2.56,5.3,.2227,4.232,5.777,8.34556,9.2]))

df = pd.DataFrame(licks["E"])
df_offset = pd.DataFrame(licks["F"])

jsonified_df = df.to_json(orient='split')

df_new = pd.read_json(jsonified_df, orient='split')

lickdata = tp.lickcalc(df[0].tolist(), offset=df_offset[0].tolist())



# fig = px.histogram(lickdata["bLicks"])

# fig.show()
# with open(file, "rb") as f:
#     variables = parse_medfile(f)

# data_array = {}
# for v in variables:
#     df = pd.DataFrame(variables[v], columns=['licks'])
#     data_array[v] = df.to_json(orient='split')
    
# jsonified_dict = json.dumps(data_array)

# reloaded_dict = json.loads(jsonified_dict)

# reloaded_df = pd.read_json(reloaded_dict["B"] , orient='split')

            
    
    
    
#     # loops through variables from medfile
#     if sum(np.diff(variables[v]) < 0) == 0: # checks tio make sure that numbers are increasing
#         try:
#             array_len_diff = np.abs(len(variables[v]) - len(data_array[str(idx-1)]))
#             if array_len_diff == 0:
#                 data_array[str(idx-1)]["offset"] = variables[v]
#             elif array_len_diff == 1:
#                 if variables[v][0] - data_array[str(idx-1)]["onset"][0] > 1:
#                     data_array[str(idx-1)]["offset"] = variables[v][:-1]
#                 elif variables[v][0] - data_array[str(idx-1)]["onset"][0] < 1:
#                     print("Need to sort this, delete first value from previous df")
#             else:
                
#         except:
#             df = pd.DataFrame(variables[v], columns=['onset'])
#             data_array[str(idx)] = df
            

# array_lengths = {key: len(variables[key]) for key in variables}

# data_array = {}
# 
# for idx, v in enumerate(variables):
#     print(used_variables)
#     if v in used_variables:
#         pass
#     else:
#         df = pd.DataFrame(variables[v], columns=['onset'])
#         used_variables.append(v)
#         for 
        
