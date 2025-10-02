import base64
import datetime
import io
import string
import json

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
from dash.exceptions import PreventUpdate

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np

from helperfx import parse_medfile, lickCalc

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dcc.Store(id='lick-data'),
    dcc.Store(id='data-store'),
    html.Div(
    [
        dbc.Row(dbc.Col(html.H1("LickCalc GUI"), width='auto')),
        dbc.Row(
            dbc.Col(html.Div(
                '''
                    This app lets you load in timestamps of licks from behavioral
                    experiments in rodents and performs microstructure analysis
                    on it.
                '''
                             ), width="auto")
        ),
        dbc.Row(children=[
                
            dbc.Col(
                  html.Div(id='filetypeLbl', children="File type"),
                  width=1
                  ),
            dbc.Col(
                html.Div(
                dcc.Dropdown(id='input-file-type',
                              options=[
                                  {'label': 'Med Associates', 'value': 'med'},
                                  {'label': 'DD Lab', 'value': 'dd'}],
                              value='med',
                                  ),
                ), width=2
          ),
            dbc.Col(html.Div(id='fileloadLbl', children="No file loaded yet"),
                  width=3
                ),
            
            dbc.Col(
                  html.Div(id='onsetLbl', children="Onset array"),
                  width=1
                  ),
            
            dbc.Col(
                html.Div(
                    dcc.Dropdown(id='onset-array',
                                 options=[
                                     {'label': '', 'value': 'none'}],
                                 value='none')),
                width=2),

            dbc.Col(
                  html.Div(id='offsetLbl', children="Offset array"),
                  width=1
                  ),
            
            dbc.Col(
                html.Div(
                    dcc.Dropdown(id='offset-array',
                                 options=[
                                     {'label': '', 'value': 'none'}],
                                 value='none')),
                width=2),
          

          ]),
        dbc.Row(
            dbc.Col(
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    # Allow multiple files to be uploaded
                    multiple=False
                ))),
        dbc.Row(
            dbc.Col(
                dcc.Graph(id='session-fig'))),
        dbc.Row(children=[
            dbc.Col(html.Div(children="Bin size"),
                  width=1),
            dbc.Col(
                dcc.Slider(
                    id='session-bin-slider',
                    min=5,
                    max=300,
                    step=5,
                    marks={i: str(i) for i in [10, 30, 60, 120, 300]},
                    value=30),
                width=8),
            # dbc.Col(html.Div(children="xxx selected"),
            #       width=2)
            ]),
        dbc.Row(dbc.Col(html.H2("Microstructural analysis"), width='auto')),
        dbc.Row(children=[
            dbc.Col(
                dcc.Graph(id='intraburst-fig',
                          figure={
                              'layout': {'margin': dict(l=20, r=20, t=20, b=20)}
                              }),
                width=5),
            dbc.Col(
                html.Div(id='intraburst-stats',
                    children='Waiting for analysis...')),
            dbc.Col(
                dcc.Graph(id='longlicks-fig'),
                width=5),
            dbc.Col(
                html.Div(id='longlicks-stats',
                     children='Waiting for analysis...'))
    ]),
        dbc.Row(children=[
            dbc.Col(
                dcc.Graph(id='bursthist-fig'),
                width=4),
            dbc.Col(
                html.Div(id='burst-stats',
                    children='Waiting for analysis...'),
                width=2),
            dbc.Col(
                dcc.Graph(id='burstprob-fig'),
                width=4),
            dbc.Col(
                html.Div(id='weibull-stats',
                     children='Waiting for analysis...'),
                width=2)
            ]),
        dbc.Row(children=[
            dbc.Col(
                html.Div('Interburst lick interval')),
            dbc.Col(
                dcc.Slider(id='interburst-slider',              
                    min=0,
                    max=3,
                    step=0.25,
                    marks={i: str(i) for i in [0.5, 1, 1.5, 2, 2.5, 3]},
                    value=0.5)),
            dbc.Col(
                html.Div('Minimum licks/burst')),
            dbc.Col(
                dcc.Slider(id='minlicks-slider',
                           min=1, max=5,
                            marks={i: str(i) for i in [1, 2, 3, 4, 5]},
                                  value=1))
            ]),
        
        
])])
    
@app.callback(Output('data-store', 'data'),
              Output('fileloadLbl', 'children'),
              Output('onset-array', 'options'),
              Output('onset-array', 'value'),
              Output('offset-array', 'options'),
              Output('offset-array', 'value'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              State('input-file-type', 'value'))
def load_and_clean_data(list_of_contents, list_of_names, list_of_dates, input_file_type):

    if list_of_contents is None:
        raise PreventUpdate
    else:
        content_type, content_string = list_of_contents.split(',')
        decoded = base64.b64decode(content_string)
        f = io.StringIO(decoded.decode('utf-8'))
        
        if input_file_type == 'med':
            variables = parse_medfile(f)
            
            data_array = {}
            for v in variables:
                df = pd.DataFrame(variables[v], columns=['licks'])
                data_array[v] = df.to_json(orient='split')
                
            options = [{'label': key, 'value': key} for key in data_array]
            value = options[0]['value']
        
        jsonified_dict = json.dumps(data_array)
            
        return jsonified_dict, list_of_names, options, value, options, value

@app.callback(Output('lick-data', 'data'),
              Input('data-store', 'data'),
              Input('onset-array', 'value'))
def get_lick_data(jsonified_dict, df_key):
    if jsonified_dict is None:
        raise PreventUpdate
    
    data_array = json.loads(jsonified_dict)
    jsonified_df = data_array[df_key]

    return jsonified_df

@app.callback(Output('session-fig', 'figure'),
              Input('lick-data', 'data'),
              Input('session-bin-slider', 'value'))
def make_session_graph(jsonified_df, binsize):
    
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(jsonified_df, orient='split')
        
        lastlick=max(df["licks"])
        
        fig = px.histogram(df,
                        range_x=[0, lastlick],
                        nbins=int(lastlick/binsize))
    
        fig.update_layout(transition_duration=500,
            xaxis_title="Time (s)",
            yaxis_title="Licks per {} s".format(binsize),
            showlegend=False)

        return fig

@app.callback(Output('intraburst-fig', 'figure'),
              Output('intraburst-stats', 'children'),
              Input('lick-data', 'data'))
def make_intraburstfreq_graph(jsonified_df):
    if jsonified_df is None:
        raise PreventUpdate
    else:        
        df = pd.read_json(jsonified_df, orient='split')
        lickdata = lickCalc(df["licks"].to_list())
        
        ilis = lickdata["ilis"]
        freq = lickdata['freq']
    
        fig = px.histogram(ilis,
                        range_x=[0, 0.5],
                        nbins=50)
    
        fig.update_layout(
            transition_duration=500,
            title="Intraburst lick frequency",
            xaxis_title="Interlick interval (s)",
            yaxis_title="Frequency",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20))
        
        stats="Frequency: {:.2f} Hz".format(freq)
        
        return fig, stats

@app.callback(Output('bursthist-fig', 'figure'),
              Output('burst-stats', 'children'),
              Input('lick-data', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'))
def make_bursthist_graph(jsonified_df, ibi, minlicks):
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(jsonified_df, orient='split')
        lickdata = lickCalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
    
        bursts=lickdata['bLicks']
        bNum=lickdata['bNum']
        bMean=lickdata['bMean']
        

        fig = px.histogram(bursts,
                            range_x=[1, max(bursts)],
                            nbins=int(np.max(bursts)))
        
        # fig.update_traces(mode='markers', marker_line_width=2, marker_size=10)
        
        fig.update_layout(
            transition_duration=500,
            title="Burst frequency histogram",
            xaxis_title="Frequency",
            yaxis_title="Burst size",
            showlegend=False)

        return fig , html.P(["No. of bursts: {}".format(bNum), html.Br(),
                              "Mean licks/burst: {:.2f}".format(bMean)])

@app.callback(Output('burstprob-fig', 'figure'),
              Output('weibull-stats', 'children'),
              Input('lick-data', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'))
def make_burstprob_graph(jsonified_df, ibi, minlicks):
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(jsonified_df, orient='split')
        lickdata = lickCalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
    
        x=lickdata['burstprob'][0]
        y=lickdata['burstprob'][1]
        alpha=lickdata['weib_alpha']
        beta=lickdata['weib_beta']
        rsq=lickdata['weib_rsq']

        fig = px.scatter(x=x,y=y)
        
        fig.update_traces(mode='markers', marker_line_width=2, marker_size=10)
        
        fig.update_layout(
            title="Weibull probability plot",
            xaxis_title="Burst size (n)",
            yaxis_title="Probability of burst>n",
            showlegend=False)

        return fig , html.P(["Alpha: {:.2f}".format(alpha), html.Br(),
                              "Beta: {:.2f}".format(beta), html.Br(),
                              "R-squared: {:.3f}".format(rsq)])

if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_hot_reload=True)
    
"""
TO DO:
    
    1. deal with files that don't work, error handling
    2. need to read medfiles properly
        get all arrays that are more than 1 element
        test for increasing arrays and only keep those ones
        find ones that might be offsets
        return arrays as dictionary of dfs
    3. deal with long licks
    4. when more than 1 list of licks, read from the appropriate one
    5. margins for graphs and other customization
    6. output file with data
    7. cumulative plot for session licks
    8. change slider dynamically to match different length files, e.g. 24h data gets 1, 2, 3, 4 h etc'
    9. support for different file types
"""
    