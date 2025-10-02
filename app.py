import base64
import datetime
import io
import string
import json

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
                     get_longlick_tooltip, get_table_tooltips, get_onset_tooltip, get_offset_tooltip)
from config_manager import config

# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.GRID])

# Get app configuration
app_config = config.get_app_config()
app = dash.Dash(__name__, title=app_config['title'], prevent_initial_callbacks=True)

# Get table cells and tooltips
table_cells, table_tooltips = get_table_tooltips()

app.layout = dbc.Container([
    dcc.Store(id='lick-data'),
    dcc.Store(id='data-store'),
    dcc.Store(id='figure-data-store'),  # Store for figure underlying data
    html.Div(
    [
        dbc.Row(children=[
            
            dbc.Col(html.H1("LickCalc GUI"), width='auto'),
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
                
            dbc.Col([
                html.Div(id='filetypeLbl', children="File type"),
            ], width=1),
            dbc.Col([
                dcc.Dropdown(id='input-file-type',
                              options=[
                                  {'label': 'Med Associates', 'value': 'med'},
                                  {'label': 'CSV/TXT', 'value': 'csv'},
                                  {'label': 'DD Lab', 'value': 'dd'}],
                              value=config.get('files.default_file_type', 'med')),
            ], width=2),
            dbc.Col([
                html.Div(id='fileloadLbl', children="No file loaded yet"),
            ], width=3),
            
            dbc.Col([
                get_onset_tooltip()[0],
                get_onset_tooltip()[1],
            ], width=1),
            
            dbc.Col([
                dcc.Dropdown(id='onset-array',
                             options=[
                                 {'label': 'No file loaded', 'value': 'none'}],
                             value='none',
                             placeholder="Select onset column..."),
            ], width=2),

            dbc.Col([
                get_offset_tooltip()[0],
                get_offset_tooltip()[1],
            ], width=1),
            
            dbc.Col([
                dcc.Dropdown(id='offset-array',
                             options=[
                                 {'label': 'No file loaded', 'value': 'none'}],
                             value='none',
                             placeholder="Select offset column..."),
            ], width=2),
          
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
                    value=config.get('session.fig_type', 'hist'))
                ),
            dbc.Col(get_binsize_tooltip()[0], width=2),
            get_binsize_tooltip()[1],
            dbc.Col(
                dcc.Slider(
                    id='session-bin-slider',
                    **config.get_slider_config('session_bin')),
                width=7),
            ]),
        dbc.Row(dbc.Col(html.H2("Microstructural analysis"), width='auto')),
        
        # Controls for microstructural analysis
        dbc.Row(children=[
            dbc.Col([
                get_ibi_tooltip()[0],
                get_ibi_tooltip()[1],
                dcc.Slider(id='interburst-slider',              
                    **config.get_slider_config('interburst'))
            ], width=4),
            dbc.Col([
                get_minlicks_tooltip()[0],
                get_minlicks_tooltip()[1],
                dcc.Slider(id='minlicks-slider',
                          **config.get_slider_config('minlicks'))
            ], width=4),
            dbc.Col([
                get_longlick_tooltip()[0],
                get_longlick_tooltip()[1],
                dcc.Slider(
                    id='longlick-threshold',
                    **config.get_slider_config('longlick'))
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
        
        # Data Output Section
        dbc.Row(dbc.Col(html.Hr(), width=12), style={'margin-top': '30px'}),  # Separator line
        dbc.Row(dbc.Col(html.H2("Data Output"), width='auto')),
        
        dbc.Row(children=[
            # Animal ID input
            dbc.Col([
                html.Label("Animal ID:", style={'font-weight': 'bold'}),
                dcc.Input(
                    id='animal-id-input',
                    type='text',
                    value=config.get('output.default_animal_id', 'ID1'),
                    placeholder='Enter animal ID...',
                    style={'width': '100%', 'margin-top': '5px'}
                )
            ], width=2),
            
            # Data selection checkboxes
            dbc.Col([
                html.Label("Include in Excel Export:", style={'font-weight': 'bold'}),
                dbc.Checklist(
                    id='export-data-checklist',
                    options=[
                        {'label': 'Session Histogram Data', 'value': 'session_hist'},
                        {'label': 'Intraburst Frequency Data', 'value': 'intraburst_freq'},
                        {'label': 'Lick Lengths Data', 'value': 'lick_lengths'},
                        {'label': 'Burst Histogram Data', 'value': 'burst_hist'},
                        {'label': 'Burst Probability Data', 'value': 'burst_prob'}
                    ],
                    value=['session_hist', 'intraburst_freq'],  # Default selections
                    inline=False,
                    style={'margin-top': '5px'}
                )
            ], width=4),
            
            # Output controls
            dbc.Col([
                html.Label("Export Options:", style={'font-weight': 'bold'}),
                html.Br(),
                html.Button(
                    'Export Data to Excel', 
                    id='export-btn', 
                    n_clicks=0,
                    className='btn btn-primary',
                    style={'margin-top': '10px', 'margin-right': '10px'}
                ),
                dcc.Download(id="download-excel"),
                html.Div(id='export-status', style={'margin-top': '10px'})
            ], width=3)
        ], style={'margin-bottom': '20px'}),
        
        # Results Table Section
        dbc.Row(dbc.Col(html.Hr(), width=12), style={'margin-top': '30px'}),  # Separator line
        dbc.Row(dbc.Col(html.H2("Results Summary"), width='auto')),
        
        dbc.Row(children=[
            # Add to table button
            dbc.Col([
                html.Button(
                    'Add Current Results to Table', 
                    id='add-to-table-btn', 
                    n_clicks=0,
                    className='btn btn-success',
                    style={'margin-right': '10px'}
                ),
                html.Button(
                    'Delete Selected Row', 
                    id='delete-row-btn', 
                    n_clicks=0,
                    className='btn btn-danger',
                    style={'margin-right': '10px'}
                ),
                html.Button(
                    'Export Selected Row', 
                    id='export-row-btn', 
                    n_clicks=0,
                    className='btn btn-info',
                    style={'margin-right': '10px'}
                ),
                html.Button(
                    'Export Full Table', 
                    id='export-table-btn', 
                    n_clicks=0,
                    className='btn btn-primary'
                ),
                dcc.Download(id="download-table"),
                html.Div(id='table-status', style={'margin-top': '10px'})
            ], width=12)
        ], style={'margin-bottom': '20px'}),
        
        # Results table
        dbc.Row(dbc.Col([
            dash_table.DataTable(
                id='results-table',
                columns=[
                    {'name': 'ID', 'id': 'id', 'type': 'text', 'editable': True},
                    {'name': 'Total Licks', 'id': 'total_licks', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Intraburst Freq (Hz)', 'id': 'intraburst_freq', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'N Bursts', 'id': 'n_bursts', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Mean Licks/Burst', 'id': 'mean_licks_per_burst', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                    {'name': 'Weibull Alpha', 'id': 'weibull_alpha', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'Weibull Beta', 'id': 'weibull_beta', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'Weibull R²', 'id': 'weibull_rsq', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                    {'name': 'N Long Licks', 'id': 'n_long_licks', 'type': 'numeric', 'format': {'specifier': '.0f'}},
                    {'name': 'Max Lick Duration (s)', 'id': 'max_lick_duration', 'type': 'numeric', 'format': {'specifier': '.4f'}}
                ],
                data=[],
                editable=True,
                row_selectable='single',
                selected_rows=[],
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px',
                    'fontFamily': 'Arial',
                    'fontSize': '12px'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    },
                    {
                        'if': {'filter_query': '{id} contains "Mean"'},
                        'backgroundColor': '#e6f3ff',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{id} contains "SD"'},
                        'backgroundColor': '#ffe6e6',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{id} contains "SE"'},
                        'backgroundColor': '#e6ffe6',
                        'fontWeight': 'bold'
                    },
                    {
                        'if': {'filter_query': '{id} contains "N"'},
                        'backgroundColor': '#fff2e6',
                        'fontWeight': 'bold'
                    }
                ],
                style_table={'overflowX': 'auto'}
            )
        ], width=12)),
        
        # Store for results table data
        dcc.Store(id='results-table-store', data=[]),
        
        
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
        
        # Create options for dropdowns
        column_names = list(data_array.keys())
        
        # For onset array, include all columns
        onset_options = [{'label': key, 'value': key} for key in column_names]
        
        # For offset array, include all columns plus "None" option
        offset_options = [{'label': 'None (onset only)', 'value': 'none'}] + [{'label': key, 'value': key} for key in column_names]
        
        # Set default values
        if len(column_names) > 0:
            # Try to find common column names for onsets
            onset_default = None
            for potential_name in ['licks', 'onset', 'timestamps', 'time', column_names[0]]:
                if potential_name in column_names:
                    onset_default = potential_name
                    break
            if onset_default is None:
                onset_default = column_names[0]
            
            # Try to find common column names for offsets
            offset_default = 'none'
            for potential_name in ['offset', 'offsets', 'end', 'stop']:
                if potential_name in column_names:
                    offset_default = potential_name
                    break
        else:
            onset_default = 'none'
            offset_default = 'none'
        
        jsonified_dict = json.dumps(data_array)
        
        file_info = f"Loaded: {list_of_names} ({len(column_names)} columns)"
            
        return jsonified_dict, file_info, onset_options, onset_default, offset_options, offset_default

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

# Data collection callback to store figure data for export
@app.callback(Output('figure-data-store', 'data'),
              Input('lick-data', 'data'),
              Input('session-bin-slider', 'value'),
              Input('interburst-slider', 'value'),
              Input('minlicks-slider', 'value'),
              Input('longlick-threshold', 'value'),
              State('data-store', 'data'),
              State('offset-array', 'value'))
def collect_figure_data(jsonified_df, bin_size, ibi, minlicks, longlick_th, jsonified_dict, offset_key):
    """Collect underlying data from all figures for export"""
    if jsonified_df is None:
        raise PreventUpdate
    
    figure_data = {}
    
    try:
        df = pd.read_json(io.StringIO(jsonified_df), orient='split')
        lick_times = df["licks"].to_list()
        
        # Session histogram data
        lastlick = max(lick_times)
        hist_counts, hist_edges = np.histogram(lick_times, bins=int(lastlick/bin_size), range=(0, lastlick))
        hist_centers = (hist_edges[:-1] + hist_edges[1:]) / 2
        figure_data['session_hist'] = {
            'bin_centers': hist_centers.tolist(),
            'counts': hist_counts.tolist(),
            'bin_size_seconds': bin_size
        }
        
        # Intraburst frequency data (ILIs)
        lickdata = lickCalc(lick_times)
        ilis = lickdata["ilis"]
        ili_counts, ili_edges = np.histogram(ilis, bins=50, range=(0, 0.5))
        ili_centers = (ili_edges[:-1] + ili_edges[1:]) / 2
        figure_data['intraburst_freq'] = {
            'ili_centers': ili_centers.tolist(),
            'counts': ili_counts.tolist(),
            'raw_ilis': ilis
        }
        
        # Initialize lick lengths data as None
        figure_data['lick_lengths'] = None
        
        # Burst data
        burst_lickdata = lickCalc(lick_times, burstThreshold=ibi, minburstlength=minlicks)
        bursts = burst_lickdata['bLicks']
        
        # Burst histogram data
        burst_counts, burst_edges = np.histogram(bursts, bins=int(np.max(bursts)), range=(1, max(bursts)))
        burst_centers = (burst_edges[:-1] + burst_edges[1:]) / 2
        figure_data['burst_hist'] = {
            'burst_sizes': burst_centers.tolist(),
            'counts': burst_counts.tolist(),
            'raw_burst_sizes': bursts
        }
        
        # Burst probability data
        x_prob, y_prob = burst_lickdata['burstprob']
        figure_data['burst_prob'] = {
            'burst_sizes': x_prob,
            'probabilities': y_prob
        }
        
        # Summary statistics
        figure_data['summary_stats'] = {
            'total_licks': burst_lickdata['total'],
            'intraburst_freq': burst_lickdata['freq'],
            'n_bursts': burst_lickdata['bNum'],
            'mean_licks_per_burst': burst_lickdata['bMean'],
            'weibull_alpha': burst_lickdata['weib_alpha'],
            'weibull_beta': burst_lickdata['weib_beta'],
            'weibull_rsq': burst_lickdata['weib_rsq'],
            'n_long_licks': 'N/A (requires offset data)',
            'max_lick_duration': 'N/A (requires offset data)'
        }
        
        # Process offset data if available for lick lengths and long lick statistics
        if offset_key and offset_key != 'none' and jsonified_dict:
            try:
                data_array = json.loads(jsonified_dict)
                offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                offset_times = offset_df["licks"].to_list()
                
                # Adjust arrays if needed
                onset_times = lick_times.copy()
                if len(onset_times) - len(offset_times) == 1:
                    onset_times = onset_times[:-1]
                elif len(onset_times) != len(offset_times):
                    onset_times = onset_times[:len(offset_times)]
                    
                if len(onset_times) == len(offset_times):
                    lickdata_with_offset = lickCalc(onset_times, offset=offset_times, longlickThreshold=longlick_th)
                    licklength = lickdata_with_offset["licklength"]
                    
                    # Create lick lengths histogram data
                    ll_counts, ll_edges = np.histogram(licklength, bins=np.arange(0, longlick_th, 0.01))
                    ll_centers = (ll_edges[:-1] + ll_edges[1:]) / 2
                    figure_data['lick_lengths'] = {
                        'duration_centers': ll_centers.tolist(),
                        'counts': ll_counts.tolist(),
                        'raw_durations': licklength,
                        'threshold': longlick_th
                    }
                    
                    # Update long lick statistics in summary
                    figure_data['summary_stats']['n_long_licks'] = len(lickdata_with_offset["longlicks"])
                    figure_data['summary_stats']['max_lick_duration'] = np.max(licklength)
                    
                    print(f"DEBUG: Calculated n_long_licks = {figure_data['summary_stats']['n_long_licks']}")
                    print(f"DEBUG: Calculated max_lick_duration = {figure_data['summary_stats']['max_lick_duration']}")
                    
            except Exception as e:
                print(f"Error processing offset data: {e}")
                figure_data['summary_stats']['n_long_licks'] = 'N/A (error)'
                figure_data['summary_stats']['max_lick_duration'] = 'N/A (error)'
        
    except Exception as e:
        print(f"Error collecting figure data: {e}")
        figure_data = {}
    
    return figure_data

# Excel export callback
@app.callback(Output("download-excel", "data"),
              Output("export-status", "children"),
              Input('export-btn', 'n_clicks'),
              State('animal-id-input', 'value'),
              State('export-data-checklist', 'value'),
              State('figure-data-store', 'data'),
              prevent_initial_call=True)
def export_to_excel(n_clicks, animal_id, selected_data, figure_data):
    """Export selected data to Excel with multiple sheets"""
    if n_clicks == 0 or not figure_data:
        raise PreventUpdate
    
    try:
        # Create Excel writer object
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"LickCalc_Export_{animal_id}_{timestamp}.xlsx"
        
        # Create a BytesIO buffer
        import io
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main summary sheet
            if 'summary_stats' in figure_data:
                stats = figure_data['summary_stats']
                summary_df = pd.DataFrame([
                    ['Animal ID', animal_id],
                    ['Export Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    ['Total Licks', stats.get('total_licks', 'N/A')],
                    ['Intraburst Frequency (Hz)', f"{stats.get('intraburst_freq', 'N/A'):.3f}" if stats.get('intraburst_freq') else 'N/A'],
                    ['Number of Bursts', stats.get('n_bursts', 'N/A')],
                    ['Mean Licks per Burst', f"{stats.get('mean_licks_per_burst', 'N/A'):.2f}" if stats.get('mean_licks_per_burst') else 'N/A'],
                    ['Weibull Alpha', f"{stats.get('weibull_alpha', 'N/A'):.3f}" if stats.get('weibull_alpha') else 'N/A'],
                    ['Weibull Beta', f"{stats.get('weibull_beta', 'N/A'):.3f}" if stats.get('weibull_beta') else 'N/A'],
                    ['Weibull R-squared', f"{stats.get('weibull_rsq', 'N/A'):.3f}" if stats.get('weibull_rsq') else 'N/A'],
                    ['Number of Long Licks', stats.get('n_long_licks', 'N/A')],
                    ['Maximum Lick Duration (s)', f"{stats.get('max_lick_duration', 'N/A'):.4f}" if isinstance(stats.get('max_lick_duration'), (int, float)) else stats.get('max_lick_duration', 'N/A')]
                ], columns=['Property', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Export selected figure data
            if 'session_hist' in selected_data and 'session_hist' in figure_data:
                data = figure_data['session_hist']
                df = pd.DataFrame({
                    'Time_Bin_Center_s': data['bin_centers'],
                    'Lick_Count': data['counts']
                })
                df.to_excel(writer, sheet_name='Session_Histogram', index=False)
            
            if 'intraburst_freq' in selected_data and 'intraburst_freq' in figure_data:
                data = figure_data['intraburst_freq']
                df = pd.DataFrame({
                    'ILI_Bin_Center_s': data['ili_centers'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Intraburst_Frequency', index=False)
            
            if 'lick_lengths' in selected_data and figure_data.get('lick_lengths'):
                data = figure_data['lick_lengths']
                df = pd.DataFrame({
                    'Duration_Bin_Center_s': data['duration_centers'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Lick_Lengths', index=False)
            
            if 'burst_hist' in selected_data and 'burst_hist' in figure_data:
                data = figure_data['burst_hist']
                df = pd.DataFrame({
                    'Burst_Size': data['burst_sizes'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Burst_Histogram', index=False)
            
            if 'burst_prob' in selected_data and 'burst_prob' in figure_data:
                data = figure_data['burst_prob']
                df = pd.DataFrame({
                    'Burst_Size': data['burst_sizes'],
                    'Probability': data['probabilities']
                })
                df.to_excel(writer, sheet_name='Burst_Probability', index=False)
        
        # Get the value from the buffer
        output.seek(0)
        excel_data = output.getvalue()
        
        status_msg = dbc.Alert(
            f"✅ Successfully exported data for {animal_id} to {filename}",
            color="success",
            dismissable=True,
            duration=4000
        )
        
        return dcc.send_bytes(excel_data, filename), status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Export failed: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return None, error_msg

# Results table callbacks

# Add current results to table
@app.callback(Output('results-table-store', 'data'),
              Output('table-status', 'children'),
              Input('add-to-table-btn', 'n_clicks'),
              State('animal-id-input', 'value'),
              State('figure-data-store', 'data'),
              State('results-table-store', 'data'),
              prevent_initial_call=True)
def add_to_results_table(n_clicks, animal_id, figure_data, existing_data):
    """Add current analysis results to the results table"""
    if n_clicks == 0 or not figure_data or 'summary_stats' not in figure_data:
        raise PreventUpdate
    
    try:
        stats = figure_data['summary_stats']
        
        # Create new row
        new_row = {
            'id': animal_id or 'Unknown',
            'total_licks': stats.get('total_licks', np.nan),
            'intraburst_freq': stats.get('intraburst_freq', np.nan),
            'n_bursts': stats.get('n_bursts', np.nan),
            'mean_licks_per_burst': stats.get('mean_licks_per_burst', np.nan),
            'weibull_alpha': stats.get('weibull_alpha', np.nan),
            'weibull_beta': stats.get('weibull_beta', np.nan),
            'weibull_rsq': stats.get('weibull_rsq', np.nan),
            'n_long_licks': stats.get('n_long_licks', np.nan) if isinstance(stats.get('n_long_licks'), (int, float)) else np.nan,
            'max_lick_duration': stats.get('max_lick_duration', np.nan) if isinstance(stats.get('max_lick_duration'), (int, float)) else np.nan
        }
        
        # Add to existing data
        updated_data = existing_data.copy() if existing_data else []
        updated_data.append(new_row)
        
        status_msg = dbc.Alert(
            f"✅ Added results for {animal_id} to table",
            color="success",
            dismissable=True,
            duration=3000
        )
        
        return updated_data, status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Failed to add results: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return existing_data, error_msg

# Update table display with statistics
@app.callback(Output('results-table', 'data'),
              Input('results-table-store', 'data'))
def update_results_table(stored_data):
    """Update the displayed table with stored data plus statistics"""
    if not stored_data:
        return []
    
    # Create copy of data
    table_data = stored_data.copy()
    
    # Calculate statistics (ignoring NaN values)
    if len(table_data) > 1:  # Only add stats if there's more than one row
        numeric_columns = ['total_licks', 'intraburst_freq', 'n_bursts', 'mean_licks_per_burst', 
                          'weibull_alpha', 'weibull_beta', 'weibull_rsq', 'n_long_licks', 'max_lick_duration']
        
        # Convert data to DataFrame for easier calculation
        df = pd.DataFrame(table_data)
        
        # Calculate statistics
        stats_rows = []
        
        # Mean
        mean_row = {'id': 'Mean'}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                mean_val = values.mean()
                mean_row[col] = mean_val if not pd.isna(mean_val) else np.nan
        stats_rows.append(mean_row)
        
        # Standard Deviation
        sd_row = {'id': 'SD'}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                sd_val = values.std()
                sd_row[col] = sd_val if not pd.isna(sd_val) else np.nan
        stats_rows.append(sd_row)
        
        # N (count of non-NaN values)
        n_row = {'id': 'N'}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                n_val = values.count()
                n_row[col] = n_val
        stats_rows.append(n_row)
        
        # Standard Error
        se_row = {'id': 'SE'}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                sd_val = values.std()
                n_val = values.count()
                se_val = sd_val / np.sqrt(n_val) if n_val > 0 and not pd.isna(sd_val) else np.nan
                se_row[col] = se_val if not pd.isna(se_val) else np.nan
        stats_rows.append(se_row)
        
        # Add separator and stats
        table_data.extend(stats_rows)
    
    return table_data

# Delete selected row
@app.callback(Output('results-table-store', 'data', allow_duplicate=True),
              Output('table-status', 'children', allow_duplicate=True),
              Input('delete-row-btn', 'n_clicks'),
              State('results-table', 'selected_rows'),
              State('results-table-store', 'data'),
              prevent_initial_call=True)
def delete_selected_row(n_clicks, selected_rows, stored_data):
    """Delete selected row from the results table"""
    if n_clicks == 0 or not selected_rows or not stored_data:
        raise PreventUpdate
    
    try:
        selected_idx = selected_rows[0]
        
        # Don't allow deletion of statistics rows
        if selected_idx >= len(stored_data):
            error_msg = dbc.Alert(
                "❌ Cannot delete statistics rows",
                color="warning",
                dismissable=True,
                duration=3000
            )
            return stored_data, error_msg
        
        # Remove the selected row
        updated_data = stored_data.copy()
        deleted_id = updated_data[selected_idx].get('id', 'Unknown')
        del updated_data[selected_idx]
        
        status_msg = dbc.Alert(
            f"✅ Deleted row for {deleted_id}",
            color="info",
            dismissable=True,
            duration=3000
        )
        
        return updated_data, status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Failed to delete row: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return stored_data, error_msg

# Export selected row
@app.callback(Output("download-table", "data"),
              Output('table-status', 'children', allow_duplicate=True),
              Input('export-row-btn', 'n_clicks'),
              Input('export-table-btn', 'n_clicks'),
              State('results-table', 'selected_rows'),
              State('results-table-store', 'data'),
              prevent_initial_call=True)
def export_table_data(export_row_clicks, export_table_clicks, selected_rows, stored_data):
    """Export selected row or full table to Excel"""
    ctx = dash.callback_context
    if not ctx.triggered or not stored_data:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if button_id == 'export-row-btn':
            if not selected_rows:
                error_msg = dbc.Alert(
                    "❌ Please select a row to export",
                    color="warning",
                    dismissable=True,
                    duration=3000
                )
                return None, error_msg
            
            selected_idx = selected_rows[0]
            if selected_idx >= len(stored_data):
                error_msg = dbc.Alert(
                    "❌ Cannot export statistics rows individually",
                    color="warning",
                    dismissable=True,
                    duration=3000
                )
                return None, error_msg
            
            # Export single row
            export_data = [stored_data[selected_idx]]
            row_id = export_data[0].get('id', 'Unknown')
            filename = f"LickCalc_SingleRow_{row_id}_{timestamp}.xlsx"
            success_msg = f"✅ Exported row for {row_id}"
            
        else:  # export-table-btn
            # Export full table
            export_data = stored_data.copy()
            filename = f"LickCalc_ResultsTable_{timestamp}.xlsx"
            success_msg = f"✅ Exported full table ({len(stored_data)} rows)"
        
        # Create Excel file
        df = pd.DataFrame(export_data)
        
        # Create a BytesIO buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
        
        output.seek(0)
        excel_data = output.getvalue()
        
        status_msg = dbc.Alert(
            success_msg,
            color="success",
            dismissable=True,
            duration=4000
        )
        
        return dcc.send_bytes(excel_data, filename), status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Export failed: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return None, error_msg

if __name__ == '__main__':
    app.run(debug=app_config['debug'], dev_tools_hot_reload=app_config['hot_reload'])
    
"""
TO DO:
    make stats look attractive, table maybe? maybe collect all stats on right hand side and have graphs next to each other??
    Add log scale option for y axis on intraburst frequency
    
    1. deal with files that don't work, error handling
    2. go through and sort out naming of variables
    5. margins for graphs and other customization
    8. change slider dynamically to match different length files, e.g. 24h data gets 1, 2, 3, 4 h etc'
    11. header rows for csvs, dd lab
    12. multiple sessions in medfiles
    13. naming of arrays/columns
    14. scale x-axis for different file lengths
    16. make histograms look the same, i.e. space between bars

    
For the histogram bin size, specify if its in minutes or seconds
"intraburst lick frequency" is average number of licks / second, might be nice to have that as a description somewhere to make it super clear what it is

Would be nice to have the sliders for setting intraburst lick interval and minimum licks/burst higher on the page
Maybe an explanation of what the Weibul plot is?
Definition of what a "long lick" is? And perhaps an option to set that, and an option to remove long licks from the data?

    
    
    
"""
    