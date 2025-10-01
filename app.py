import base64
import datetime
import io
import string
import json
import csv

import dash
from dash import dcc, html, dash_table, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np

from helperfx import parse_medfile, parse_csvfile, parse_ddfile, lickCalc
from tooltips import (get_binsize_tooltip, get_ibi_tooltip, get_minlicks_tooltip, 
                     get_longlick_tooltip, get_table_tooltips)

# template_df = pd.DataFrame(data=None, columns=["Property", "Value"])

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.GRID])

app = dash.Dash(__name__, title='LickCalc', prevent_initial_callbacks=True)

# Get table cells and tooltips
table_cells, table_tooltips = get_table_tooltips()

app.layout = dbc.Container([
    dcc.Store(id='lick-data'),
    dcc.Store(id='data-store'),
    html.Div(
    [
        dbc.Row(children=[
            
            dbc.Col(html.H1("LickCalc GUI"), width='auto'),
            dbc.Col([html.Button('Output file', id='btn', n_clicks=0), dcc.Download(id="download")])
                    ]),
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
                                  {'label': 'CSV/TXT', 'value': 'csv'},
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
            dbc.Col(
                dcc.RadioItems(
                    id='session-fig-type',
                    options=[
                        {"label": "Standard histogram", "value": "hist"},
                        {"label": "Cumulative plot", "value": "cumul"}],
                    value="hist")
                ),
            dbc.Col(get_binsize_tooltip()[0], width=2),
            get_binsize_tooltip()[1],
            dbc.Col(
                dcc.Slider(
                    id='session-bin-slider',
                    min=5,
                    max=300,
                    step=5,
                    marks={i: str(i) for i in [10, 30, 60, 120, 300]},
                    value=30),
                width=7),
            ]),
        dbc.Row(dbc.Col(html.H2("Microstructural analysis"), width='auto')),
        
        # Controls for microstructural analysis
        dbc.Row(children=[
            dbc.Col([
                get_ibi_tooltip()[0],
                get_ibi_tooltip()[1],
                dcc.Slider(id='interburst-slider',              
                    min=0,
                    max=3,
                    step=0.25,
                    marks={i: str(i) for i in [0.5, 1, 1.5, 2, 2.5, 3]},
                    value=0.5)
            ], width=4),
            dbc.Col([
                get_minlicks_tooltip()[0],
                get_minlicks_tooltip()[1],
                dcc.Slider(id='minlicks-slider',
                           min=1, max=5,
                            marks={i: str(i) for i in [1, 2, 3, 4, 5]},
                                  value=1)
            ], width=4),
            dbc.Col([
                get_longlick_tooltip()[0],
                get_longlick_tooltip()[1],
                dcc.Slider(
                    id='longlick-threshold',
                    min=0.1,
                    max=1.0,
                    step=0.1,
                    marks={i: str(i) for i in [0.2, 0.4, 0.6, 0.8, 1.0]},
                    value=0.3)
            ], width=4),
        ], style={'margin-bottom': '20px'}),
        
        dbc.Row(children=[
            dbc.Col(
                dcc.Graph(id='intraburst-fig'),
                width=4),
            dbc.Col(
                dcc.Graph(id='longlicks-fig'),
                width=4),
            dbc.Col([
                dbc.Table([
                    html.Tr([html.Th("Property"), html.Th("Value")]),
                    html.Tr([table_cells[0], html.Td(id="total-licks")]),  # Total licks
                    html.Tr([table_cells[1], html.Td(id="intraburst-freq")]),  # Intraburst frequency
                    html.Tr([table_cells[2], html.Td(id="nlonglicks")]),  # No. of long licks
                    html.Tr([html.Td("Maximum long lick"), html.Td(id="longlicks-max")]),
                    ],
                    striped=True, hover=True, bordered=True),
                # Add tooltips
                table_tooltips[0],  # Total licks tooltip
                table_tooltips[1],  # Intraburst frequency tooltip
                table_tooltips[2],  # No. of long licks tooltip
            ], width=4),
    ]),
        
        dbc.Row(children=[
            dbc.Col(
                dcc.Graph(id='bursthist-fig'),
                width=4),
            dbc.Col(
                dcc.Graph(id='burstprob-fig'),
                width=4),
            dbc.Col([
                dbc.Table([
                    html.Tr([html.Th("Property"), html.Th("Value")]),
                    html.Tr([html.Td("No. of bursts"), html.Td(id="nbursts")]),
                    html.Tr([table_cells[3], html.Td(id="licks-per-burst")]),  # Mean licks per burst
                    html.Tr([table_cells[4], html.Td(id="weibull-alpha")]),  # Weibull: Alpha
                    html.Tr([table_cells[5], html.Td(id="weibull-beta")]),  # Weibull: Beta
                    html.Tr([table_cells[6], html.Td(id="weibull-rsq")]),  # Weibull: r-squared
                    ],
                    striped=True, hover=True, bordered=True),
                # Add tooltips
                table_tooltips[3],  # Mean licks per burst tooltip
                table_tooltips[4],  # Weibull: Alpha tooltip
                table_tooltips[5],  # Weibull: Beta tooltip
                table_tooltips[6],  # Weibull: r-squared tooltip
            ], width=4),
            
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
            data_array = parse_medfile(f)
        elif input_file_type == 'csv':
            data_array = parse_csvfile(f)
        elif input_file_type == 'dd':
            data_array = parse_ddfile(f)
        
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
              Input('session-fig-type', 'value'),
              Input('session-bin-slider', 'value'))
def make_session_graph(jsonified_df, figtype, binsize):
    
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        lastlick=max(df["licks"])
        
        if figtype == "hist":
            fig = px.histogram(df,
                            range_x=[0, lastlick],
                            nbins=int(lastlick/binsize))
        
            fig.update_layout(transition_duration=500,
                xaxis_title="Time (s)",
                yaxis_title="Licks per {} s".format(binsize),
                showlegend=False)
        else:
            fig = px.line(x=df["licks"], y=range(0, len(df["licks"])))
            
            fig.update_layout(transition_duration=500,
                xaxis_title="Time (s)",
                yaxis_title="Cumulative licks",
                showlegend=False,)

        return fig

@app.callback(Output('intraburst-fig', 'figure'),
              Output('total-licks', 'children'),
              Output('intraburst-freq', 'children'),
              Input('lick-data', 'data'))
def make_intraburstfreq_graph(jsonified_df):
    if jsonified_df is None:
        raise PreventUpdate
    else:        
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        lickdata = lickCalc(df["licks"].to_list())
 
        ilis = lickdata["ilis"]

        fig = px.histogram(ilis,
                        range_x=[0, 0.5],
                        nbins=50)
    
        fig.update_layout(
            transition_duration=500,
            title="Intraburst lick frequency",
            xaxis_title="Interlick interval (s)",
            yaxis_title="Frequency",
            showlegend=False,
            # margin=dict(l=20, r=20, t=20, b=20),
            )
        
        nlicks = "{}".format(lickdata['total'])
        freq = "{:.2f} Hz".format(lickdata['freq'])
        
        return fig, nlicks, freq

@app.callback(Output('longlicks-fig', 'figure'),
              Output('nlonglicks', 'children'),
              Output('longlicks-max', 'children'),
              Input('offset-array', 'value'),
              Input('longlick-threshold', 'value'),
              State('data-store', 'data'),
              State('lick-data', 'data'),)
def make_longlicks_graph(offset_key, longlick_th, jsonified_dict, jsonified_df):
    if jsonified_df is None:
        raise PreventUpdate
    else:        
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        
        data_array = json.loads(jsonified_dict)
        offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
        
        onset=df["licks"].to_list()
        offset=offset_df["licks"].to_list()
        
        if len(onset) - len(offset) == 0:
            print("arrays are the same size, making figure...")
        elif len(onset) - len(offset) == 1:
            print("arrays are different lengths by 1, need to remove a value")
            if offset[0] > onset[0]:
                onset = onset [:-1]
        else:
            print("offset array seems wrong")
            return {"data": []}, ""
        
        lickdata = lickCalc(onset, offset=offset, longlickThreshold=longlick_th)
        licklength = lickdata["licklength"]

        max_longlick = np.max(licklength)
        
        counts, bins = np.histogram(licklength, bins=np.arange(0, longlick_th, 0.01))
        bins = 0.5 * (bins[:-1] + bins[1:])
        
        fig = px.bar(x=bins, y=counts)
    
        fig.update_layout(
            transition_duration=500,
            title="Lick lengths",
            xaxis_title="Lick length (s)",
            yaxis_title="Frequency",
            showlegend=False,
            # margin=dict(l=20, r=20, t=20, b=20),
            )
        
        nlonglicks = "{}".format(len(lickdata["longlicks"]))
        longlick_max = "{:.2f}".format(np.max(licklength))
        
        return fig, nlonglicks, longlick_max

@app.callback(Output('bursthist-fig', 'figure'),
              Input('lick-data', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'))
def make_bursthist_graph(jsonified_df, ibi, minlicks):
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        lickdata = lickCalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
    
        bursts=lickdata['bLicks']

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

        return fig

@app.callback(Output('burstprob-fig', 'figure'),
              Output('nbursts', 'children'),
              Output('licks-per-burst', 'children'),
              Output('weibull-alpha', 'children'),
              Output('weibull-beta', 'children'),
              Output('weibull-rsq', 'children'),
              Input('lick-data', 'data'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'))
def make_burstprob_graph(jsonified_df, ibi, minlicks):
    if jsonified_df is None:
        raise PreventUpdate
    else:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        lickdata = lickCalc(df["licks"].to_list(), burstThreshold=ibi, minburstlength=minlicks)
    
        x=lickdata['burstprob'][0]
        y=lickdata['burstprob'][1]

        fig = px.scatter(x=x,y=y)
        
        fig.update_traces(mode='markers', marker_line_width=2, marker_size=10)
        
        fig.update_layout(
            title="Weibull probability plot",
            xaxis_title="Burst size (n)",
            yaxis_title="Probability of burst>n",
            showlegend=False)

        bNum = "{}".format(lickdata['bNum'])
        bMean = "{:.2f}".format(lickdata['bMean'])      
        alpha = "{:.2f}".format(lickdata['weib_alpha'])
        beta = "{:.2f}".format(lickdata['weib_beta'])
        rsq = "{:.2f}".format(lickdata['weib_rsq'])


        return fig , bNum, bMean, alpha, beta, rsq

@app.callback(Output("download", "data"),
              Input('btn', 'n_clicks'))
def save_file(n):

    
    d = [('Filename',"hey there")]
    #              ('Total licks',self.lickdata['total']),
    #              ('Frequency',self.lickdata['freq']),
    #              ('Number of bursts',self.lickdata['bNum']),
    #              ('Licks per burst',self.lickdata['bMean']),
    #              ('Licks per burst (first 3)',self.lickdata['bMean-first3']),
    #              ('Number of long licks',len(self.lickdata['longlicks'])),
    #              ('Weibull: alpha',self.lickdata['weib_alpha']),
    #              ('Weibull: beta',self.lickdata['weib_beta']),
    #              ('Weibull: rsquared',self.lickdata['weib_rsq'])]
    # print(n)
    with open(".\\output.csv", 'w', newline='') as file:
        csv_out = csv.writer(file)
        csv_out.writerow(['Parameter', 'Value'])
        for row in d:
            csv_out.writerow(row)

if __name__ == '__main__':
    app.run(debug=True, dev_tools_hot_reload=True)
    
"""
TO DO:
    make stats look attractive, table maybe? maybe collect all stats on right hand side and have graphs next to each other??
    cumulative plot for session licks
    write total licks somewhere
    Add log scale option for y axis on intraburst frequency
    
    1. deal with files that don't work, error handling
    2. go through and sort out naming of variables
    3. 
    4. 
    5. margins for graphs and other customization
    6. output file with data
    7. 
    8. change slider dynamically to match different length files, e.g. 24h data gets 1, 2, 3, 4 h etc'
    9. 
    10. 
    11. header rows for csvs, dd lab
    12. multiple sessions in medfiles
    13. naming of arrays/columns
    14. scale x-axis for different file lengths
    15. 
    16. make histograms look the same, i.e. space between bars
    17. 
    18. 
    
    Would be great to have a way to export the data to Excel (or similar) - either option to load several mice / files and look scroll through each, and then export all the data into one file, or have a summary of important data (number of licks, number of bursts, licks per burst, etc) in a table that is easily copy/pasted into excel so it's quick to load in a file, paste the data into an excel file, load the next file, and so on.
For the histogram bin size, specify if its in minutes or seconds
"intraburst lick frequency" is average number of licks / second, might be nice to have that as a description somewhere to make it super clear what it is
Remove "spacer..."
Description of what the slider next to spacer is
Would be nice to have the sliders for setting intraburst lick interval and minimum licks/burst higher on the page
Maybe an explanation of what the Weibul plot is?
Definition of what a "long lick" is? And perhaps an option to set that, and an option to remove long licks from the data?

make sure updated lickcalc still works
write test suite to check (either in trompy or here)
add help bubbles with explanations of parameters/fields/output
    
    
    
"""
    