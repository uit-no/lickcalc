# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5 20:54:51 2021

@author: jmc010
"""
import base64
import datetime
import io
import string

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd

import trompy as tp

globaldata=[2,3,4,5,5,6,76,7,7]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

fig = px.line(globaldata)

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
       
    # dcc.Dropdown(id='input-file-type',
    #               options=[
    #                   {'label': 'Med Associates', 'value': 'med'},
    #                   {'label': 'DD Lab', 'value': 'dd'}],
    #               value='med',
    #                   ),
    
    html.Button(id='clicker', n_clicks=0, children='Submit'),
    
    html.H1(id='filename', children='Hello Dash'),
    
    dcc.Graph(id='graph', figure=fig)

    # # dcc.Store inside the app that stores the intermediate value
    # dcc.Store(id='lick-data')
    
])

# def parse_medfile(f):
    
#     sessionToExtract=1

#     f.seek(0)
#     filerows = f.readlines()[8:]
#     datarows = [tp.isnumeric(x) for x in filerows]
#     matches = [i for i,x in enumerate(datarows) if x == 0.3]
#     if sessionToExtract > len(matches):
#         print('Session ' + str(sessionToExtract) + ' does not exist.')
    
#     varstart = matches[sessionToExtract - 1]    
#     medvars = {}
   
#     k = int(varstart + 27)
#     for i in range(26):
#         medvarsN = int(datarows[varstart + i + 1])
#         if medvarsN > 1:
#             medvars[string.ascii_uppercase[i]] = datarows[k:k + int(medvarsN)]
#         k = k + medvarsN

#     for val in medvars.values():
#         val.pop(0)

#     return medvars


# @app.callback(Output('lick-data', 'data'),
#               Input('upload-data', 'contents'),
#               State('upload-data', 'filename'),
#               State('upload-data', 'last_modified'),
#               State('input-file-type', 'value'))
# def load_and_clean_data(list_of_contents, list_of_names, list_of_dates, input_file_type):
#     if list_of_contents is None:
#         raise PreventUpdate
#     else:
#         content_type, content_string = list_of_contents.split(',')
#         decoded = base64.b64decode(content_string)
#         f = io.StringIO(decoded.decode('utf-8'))
        
#         if input_file_type == 'med':
#             print('Med file expected...')
#             data = parse_medfile(f)
#             # Need to get all med arrays and assign properly, deal with offset licks etc
#             df = pd.DataFrame(data["E"])
            
#             print(df)
        
#         # lick_dictionary = tp.lickCalc(data)
        
#         jsonified_df = df.to_json(orient='split')
            
#         return jsonified_df

@app.callback(Output('graph', 'figure'),
              Output('filename', 'children'),
              Input('clicker', 'n_clicks'))
def make_session_graph(n_clicks):
    if n_clicks == 1:
    # df = pd.read_json(jsonified_df, orient='split')
    # lickdata = tp.lickCalc(df[0].to_list())
    
        fig = go.Figure(data=[go.Scatter(x=[], y=[])])
        # fig.update_traces()
        # fig.update_layout()
    
    #fig = go.Scatter(x=[2,3,4], y=[4,8,6])
    # fig.show()
    # fig.update_layout(transition_duration=500)
    
    # fig.show()
    
        print("is this working")
        return fig, "hey there"
    else:
        
        fig = px.line([4,8,6])
        
        return fig, "boo"
    
    
    

if __name__ == '__main__':
#    app.run_server(debug=True, dev_tools_hot_reload=False)
    app.run_server(debug=True)
